import json

from app.answer import ABSTAIN_MESSAGE, AnswerService
from app.audit import AuditLog
from app.chunking import Chunk
from app.llm import ExtractiveLLM, LLMReply
from app.retrieval import Hit
from app.verify import Claim

CHUNK = Chunk("01", "Cấp 1", "Tổng giao dịch mỗi ngày: 5.000.000 đồng.")


class FixedSearcher:
    def __init__(self, hits: list[Hit]) -> None:
        self.hits, self.queries = hits, []

    def search(self, query, k=5, mode="hybrid"):
        self.queries.append(query)
        return self.hits


class ScriptedLLM:
    name = "scripted"

    def __init__(self, reply: LLMReply) -> None:
        self.reply, self.seen = reply, []

    def complete(self, question, passages):
        self.seen.append(question)
        return self.reply


def hits() -> list[Hit]:
    return [Hit(0, CHUNK, 1.0, 1)]


def test_supported_answer_is_returned_with_citation():
    llm = ScriptedLLM(LLMReply(True, [Claim("Tối đa 5.000.000 đồng mỗi ngày", 1, "Tổng giao dịch mỗi ngày: 5.000.000 đồng.")]))
    result = AnswerService(FixedSearcher(hits()), llm).ask("Hạn mức cấp 1?")
    assert not result.abstained and "[1]" in result.answer
    assert result.citations[0].doc_id == "01"


def test_unsupported_claim_is_dropped_and_service_abstains():
    llm = ScriptedLLM(LLMReply(True, [Claim("Tối đa 9.000.000 đồng mỗi ngày", 1, "Tổng giao dịch mỗi ngày: 9.000.000 đồng.")]))
    result = AnswerService(FixedSearcher(hits()), llm).ask("Hạn mức cấp 1?")
    assert result.abstained and result.answer == ABSTAIN_MESSAGE
    assert result.reason == "no_claim_survived_verification" and len(result.dropped) == 1


def test_verifier_can_be_switched_off_for_ablation():
    llm = ScriptedLLM(LLMReply(True, [Claim("Tối đa 9.000.000 đồng mỗi ngày", 1, "Tổng giao dịch mỗi ngày: 9.000.000 đồng.")]))
    result = AnswerService(FixedSearcher(hits()), llm, verify=False).ask("Hạn mức cấp 1?")
    assert not result.abstained


def test_model_saying_unanswerable_means_abstain():
    result = AnswerService(FixedSearcher(hits()), ScriptedLLM(LLMReply(False, []))).ask("Hotline?")
    assert result.abstained and result.reason == "model_found_no_answer"


def test_no_passages_means_abstain_without_calling_the_model():
    llm = ScriptedLLM(LLMReply(True, []))
    result = AnswerService(FixedSearcher([]), llm).ask("Thời tiết?")
    assert result.abstained and result.reason == "no_passages" and llm.seen == []


def test_raw_pii_never_reaches_search_model_or_audit_log(tmp_path):
    searcher, llm = FixedSearcher(hits()), ScriptedLLM(LLMReply(False, []))
    log = AuditLog(tmp_path / "audit.jsonl")
    AnswerService(searcher, llm, log).ask("SĐT 0912345678, CCCD 079012345678 bị khóa")
    everything = json.dumps([searcher.queries, llm.seen]) + (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "0912345678" not in everything and "079012345678" not in everything
    assert "[SDT]" in everything and "[CCCD]" in everything


def test_extractive_baseline_answers_from_the_best_sentence():
    reply = ExtractiveLLM().complete(
        "Tổng giao dịch mỗi ngày của tài khoản cấp 1", ["Cấp 1\nTổng giao dịch mỗi ngày: 5.000.000 đồng."]
    )
    assert reply.answerable and "5.000.000" in reply.claims[0].text
