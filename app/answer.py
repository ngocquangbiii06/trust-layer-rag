"""The question-answering pipeline: mask, retrieve, generate, verify, abstain, audit."""

import time
from dataclasses import dataclass, field
from typing import Protocol

from app.audit import AuditLog
from app.corpus import doc_title
from app.llm import LLM
from app.pii import mask_pii
from app.retrieval import Hit
from app.verify import Verdict, verify_claims

ABSTAIN_MESSAGE = "Mình chưa tìm thấy căn cứ trong tài liệu chính sách để trả lời câu hỏi này."
DEFAULT_TOP_K = 4  # passages sent to the model for one question


class Searcher(Protocol):
    def search(self, query: str, k: int = 5, mode: str = "hybrid") -> list[Hit]: ...


@dataclass
class Citation:
    id: int
    doc_id: str
    doc_title: str
    heading: str
    quote: str


@dataclass
class Answer:
    question_masked: str
    answer: str
    abstained: bool
    reason: str  # why it abstained, "" otherwise
    citations: list[Citation] = field(default_factory=list)
    dropped: list[Verdict] = field(default_factory=list)  # claims removed by the verifier
    pii_types: tuple[str, ...] = ()
    retrieved_docs: list[str] = field(default_factory=list)
    latency_ms: int = 0
    model: str = ""


class AnswerService:
    def __init__(
        self,
        searcher: Searcher,
        llm: LLM,
        audit: AuditLog | None = None,
        top_k: int = DEFAULT_TOP_K,
        verify: bool = True,
    ) -> None:
        self.searcher, self.llm = searcher, llm
        self.audit = audit or AuditLog(None)
        self.top_k, self.verify = top_k, verify

    def ask(self, question: str) -> Answer:
        started = time.perf_counter()
        masked = mask_pii(question)  # nothing below ever sees the raw question
        hits = self.searcher.search(masked.text, k=self.top_k)
        passages = [f"{h.chunk.heading}\n{h.chunk.text}" if h.chunk.heading else h.chunk.text for h in hits]
        result = Answer(
            question_masked=masked.text,
            answer=ABSTAIN_MESSAGE,
            abstained=True,
            reason="",
            pii_types=masked.types,
            retrieved_docs=[h.chunk.doc_id for h in hits],
            model=self.llm.name,
        )
        if not hits:
            result.reason = "no_passages"
        else:
            reply = self.llm.complete(masked.text, passages)
            if not reply.answerable or not reply.claims:
                result.reason = "model_found_no_answer"
            else:
                verdicts = verify_claims(reply.claims, passages, masked.text) if self.verify else [
                    Verdict(c, True, "") for c in reply.claims
                ]
                kept = [v.claim for v in verdicts if v.ok]
                result.dropped = [v for v in verdicts if not v.ok]
                if not kept:
                    result.reason = "no_claim_survived_verification"
                else:
                    result.abstained, result.reason = False, ""
                    result.answer = " ".join(f"{c.text} [{i}]" for i, c in enumerate(kept, 1))
                    result.citations = [
                        Citation(i, hits[c.source - 1].chunk.doc_id, doc_title(hits[c.source - 1].chunk.doc_id),
                                 hits[c.source - 1].chunk.heading, c.quote)
                        for i, c in enumerate(kept, 1)
                    ]
        result.latency_ms = int((time.perf_counter() - started) * 1000)
        self.audit.write(
            {
                "question": result.question_masked,
                "pii_types": list(result.pii_types),
                "retrieved_docs": result.retrieved_docs,
                "abstained": result.abstained,
                "reason": result.reason,
                "dropped_claims": [v.reason for v in result.dropped],
                "model": result.model,
                "latency_ms": result.latency_ms,
            }
        )
        return result
