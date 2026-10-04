"""Dense (Qdrant), sparse (BM25) and hybrid retrieval over chunks."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

from app.bm25 import BM25
from app.chunking import Chunk
from app.fusion import rrf

Mode = Literal["dense", "bm25", "hybrid"]
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CACHE_DIR = Path(__file__).resolve().parent.parent / "models_cache"
_COLLECTION = "chunks"


@dataclass(frozen=True)
class Hit:
    index: int  # position in the chunk list
    chunk: Chunk
    score: float
    rank: int  # 1 = best


def embed_text(chunk: Chunk) -> str:
    """The heading is part of the meaning, so it is embedded together with the body."""
    return f"{chunk.heading}\n{chunk.text}" if chunk.heading else chunk.text


class Retriever:
    def __init__(self, chunks: list[Chunk], model_name: str = DEFAULT_MODEL) -> None:
        self.chunks = chunks
        self.model_name = model_name
        self._model = TextEmbedding(model_name, cache_dir=str(CACHE_DIR))
        self._bm25 = BM25([embed_text(c) for c in chunks])
        vectors = list(self._model.embed([embed_text(c) for c in chunks]))
        self._client = QdrantClient(":memory:")
        self._client.create_collection(
            _COLLECTION,
            vectors_config=models.VectorParams(size=len(vectors[0]), distance=models.Distance.COSINE),
        )
        self._client.upsert(
            _COLLECTION,
            points=[
                models.PointStruct(id=i, vector=v.tolist(), payload={"doc_id": c.doc_id})
                for i, (c, v) in enumerate(zip(chunks, vectors, strict=True))
            ],
        )

    def _dense(self, query: str, k: int) -> list[tuple[int, float]]:
        vector = next(iter(self._model.embed([query]))).tolist()
        response = self._client.query_points(_COLLECTION, query=vector, limit=k)
        return [(int(p.id), float(p.score)) for p in response.points]

    def search(self, query: str, k: int = 5, mode: Mode = "hybrid") -> list[Hit]:
        if mode == "dense":
            ranked = self._dense(query, k)
        elif mode == "bm25":
            ranked = self._bm25.top(query, k)
        else:
            pool = max(k * 3, 15)
            dense_ids = [i for i, _ in self._dense(query, pool)]
            sparse_ids = [i for i, _ in self._bm25.top(query, pool)]
            ranked = rrf([dense_ids, sparse_ids])[:k]
        return [Hit(i, self.chunks[i], score, rank) for rank, (i, score) in enumerate(ranked, 1)]
