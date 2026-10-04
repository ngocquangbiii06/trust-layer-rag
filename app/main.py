"""FastAPI service: /ask, /search, /health and a small web page."""

from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.answer import AnswerService
from app.audit import AuditLog
from app.corpus import load_chunks
from app.llm import default_llm
from app.pii import mask_pii
from app.retrieval import Retriever

app = FastAPI(title="Trust-layer RAG", version="0.1.0")
_STATIC = Path(__file__).resolve().parent / "static"


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


@lru_cache(maxsize=1)
def retriever() -> Retriever:
    return Retriever(load_chunks())


@lru_cache(maxsize=1)
def service() -> AnswerService:
    return AnswerService(retriever(), default_llm(), AuditLog())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


@app.post("/search")
def search(request: AskRequest, k: int = 5, mode: str = "hybrid") -> dict:
    if mode not in {"dense", "bm25", "hybrid"}:
        raise HTTPException(status_code=422, detail="mode must be dense, bm25 or hybrid")
    masked = mask_pii(request.question)
    hits = retriever().search(masked.text, k=min(max(k, 1), 20), mode=mode)  # type: ignore[arg-type]
    return {
        "query": masked.text,
        "hits": [
            {"rank": h.rank, "score": round(h.score, 4), "doc_id": h.chunk.doc_id,
             "heading": h.chunk.heading, "text": h.chunk.text}
            for h in hits
        ],
    }


@app.post("/ask")
def ask(request: AskRequest) -> dict:
    try:
        result = service().ask(request.question)
    except RuntimeError as error:  # e.g. no API key configured for a live model
        raise HTTPException(status_code=503, detail=str(error)) from error
    body = asdict(result)
    body["dropped"] = [{"text": v.claim.text, "reason": v.reason} for v in result.dropped]
    return body
