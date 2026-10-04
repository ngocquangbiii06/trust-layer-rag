"""Compare retrieval configurations offline: embedding model, with and without a reranker.

Usage:  python -m eval.retrieval_compare

For every configuration, on the answerable questions:
  doc@k       an expected document is among the top k chunks (hybrid search)
  evidence@k  every key fact of the question is written in the top k chunks. This is the ceiling of
              the end-to-end system when k passages are sent to the model.
No language model is called. Writes eval/results/retrieval_compare.md.
"""

import time
from pathlib import Path

from app.corpus import load_chunks
from app.pii import mask_pii
from app.retrieval import Retriever
from eval.failures import evidence_present
from eval.retrieval_eval import load_questions

ROOT = Path(__file__).resolve().parent
MINILM = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MPNET = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
E5 = "intfloat/multilingual-e5-large"
JINA = "jinaai/jina-reranker-v2-base-multilingual"
CONFIGS = {
    "minilm": (MINILM, None),
    "mpnet": (MPNET, None),
    "e5-large": (E5, None),
    "minilm+rerank": (MINILM, JINA),
    "mpnet+rerank": (MPNET, JINA),
    "e5-large+rerank": (E5, JINA),
}
KS = (1, 3, 4, 6)


def measure(retriever: Retriever, questions: list[dict]) -> dict:
    scored = [q for q in questions if q["expect"] == "answer" and q["expected_docs"]]
    doc = {k: 0 for k in KS}
    evidence = {k: 0 for k in KS}
    started = time.perf_counter()
    for q in scored:
        hits = retriever.search(mask_pii(q["question"]).text, k=max(KS))
        for k in KS:
            top = hits[:k]
            doc[k] += bool(set(q["expected_docs"]) & {h.chunk.doc_id for h in top})
            evidence[k] += evidence_present(q, [f"{h.chunk.heading}\n{h.chunk.text}" for h in top])
    return {"n": len(scored), "doc": doc, "evidence": evidence,
            "ms": int((time.perf_counter() - started) * 1000 / len(scored))}


def main() -> None:
    chunks, questions = load_chunks(), load_questions()
    lines = ["# Retrieval configurations compared (hybrid search, no language model)", "",
             "evidence@k: every key fact of the question is in the top k chunks.", "",
             "| Config | doc@1 | doc@3 | evidence@3 | evidence@4 | evidence@6 | ms per query |",
             "|---|---|---|---|---|---|---|"]
    for name, (model, rerank) in CONFIGS.items():
        result = measure(Retriever(chunks, model, rerank), questions)
        n, d, e = result["n"], result["doc"], result["evidence"]
        row = f"| {name} | {d[1]}/{n} | {d[3]}/{n} | {e[3]}/{n} | {e[4]}/{n} | {e[6]}/{n} | {result['ms']} |"
        lines.append(row)
        print(row, flush=True)
    (ROOT / "results" / "retrieval_compare.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
