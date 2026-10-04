"""Measure retrieval quality: does the right document appear in the top k chunks?

Usage:  python -m eval.retrieval_eval [--model NAME] [--out eval/results/retrieval.md]
Only questions with expect == "answer" are scored here. Metrics:
  any@k  at least one expected document is among the documents of the top k chunks
  all@k  every expected document is among them (matters for multi-document questions)
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from app.corpus import load_chunks
from app.retrieval import DEFAULT_MODEL, Retriever

ROOT = Path(__file__).resolve().parent
KS = (1, 3, 5)
MODES = ("dense", "bm25", "hybrid")


def load_questions() -> list[dict]:
    lines = (ROOT / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def evaluate(retriever: Retriever, questions: list[dict]) -> dict[str, dict]:
    scored = [q for q in questions if q["expect"] == "answer" and q["expected_docs"]]
    results: dict[str, dict] = {}
    for mode in MODES:
        any_hits = {k: 0 for k in KS}
        all_hits = {k: 0 for k in KS}
        by_kind: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        misses = []
        for q in scored:
            hits = retriever.search(q["question"], k=max(KS), mode=mode)
            docs = [h.chunk.doc_id for h in hits]
            expected = set(q["expected_docs"])
            for k in KS:
                top = set(docs[:k])
                any_hits[k] += bool(expected & top)
                all_hits[k] += expected <= top
            ok3 = bool(expected & set(docs[:3]))
            by_kind[q["kind"]][0] += ok3
            by_kind[q["kind"]][1] += 1
            if not ok3:
                misses.append((q["id"], q["question"], sorted(expected), docs[:3]))
        results[mode] = {
            "n": len(scored),
            "any": any_hits,
            "all": all_hits,
            "by_kind": dict(by_kind),
            "misses": misses,
        }
    return results


def render(model: str, chunk_count: int, results: dict[str, dict]) -> str:
    n = next(iter(results.values()))["n"]
    lines = [
        f"# Retrieval evaluation - {model}",
        "",
        f"Chunks: {chunk_count}. Scored questions: {n} (expect == answer).",
        "",
        "| Mode | any@1 | any@3 | any@5 | all@3 | all@5 |",
        "|---|---|---|---|---|---|",
    ]
    for mode, r in results.items():
        cells = [f"{r['any'][1]}/{n}", f"{r['any'][3]}/{n}", f"{r['any'][5]}/{n}"]
        cells += [f"{r['all'][3]}/{n}", f"{r['all'][5]}/{n}"]
        lines.append(f"| {mode} | " + " | ".join(cells) + " |")
    lines += ["", "## any@3 by question kind", "", "| Kind | " + " | ".join(results) + " |"]
    lines.append("|---|" + "---|" * len(results))
    kinds = sorted({k for r in results.values() for k in r["by_kind"]})
    for kind in kinds:
        row = []
        for r in results.values():
            ok, total = r["by_kind"].get(kind, [0, 0])
            row.append(f"{ok}/{total}")
        lines.append(f"| {kind} | " + " | ".join(row) + " |")
    lines += ["", "## Misses at k=3", ""]
    for mode, r in results.items():
        lines.append(f"**{mode}**")
        if not r["misses"]:
            lines.append("- none")
        for qid, question, expected, got in r["misses"]:
            lines.append(f"- {qid} expected {expected}, got {got}: {question}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    chunks = load_chunks()
    retriever = Retriever(chunks, args.model)
    report = render(args.model, len(chunks), evaluate(retriever, load_questions()))
    slug = args.model.split("/")[-1]
    out = Path(args.out) if args.out else ROOT / "results" / f"retrieval_{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
