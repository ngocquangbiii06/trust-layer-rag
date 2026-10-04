"""Group the failures of an end-to-end run by cause, and compare the verifier on versus off.

Usage:
  python -m eval.failures --tag L0

Replays the model replies recorded in `eval/llm_cache/` (no key, no network), asks every question
twice, once with the verifier and once without, and writes two reports:
  eval/results/failures_<tag>.md        every failed question, grouped by cause
  eval/results/verify_compare_<tag>.md  what the verifier changed, question by question

Because both runs judge the very same model replies, any difference is caused by the verifier.
"""

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from app.pii import mask_pii
from app.retrieval import DEFAULT_MODEL, Retriever
from app.text import fold
from eval.answer_eval import build_llm, run
from eval.live import STAGES

ROOT = Path(__file__).resolve().parent

CATEGORIES = {
    "error": "the call failed or the reply was never recorded",
    "forbidden_claim": "the answer contains a claim it must never make (prompt injection worked)",
    "answered_should_abstain": "answered a question the documents cannot answer",
    "verifier_false_drop": "the verifier removed a claim that was needed; without the verifier the "
                           "question passes",
    "retrieval_miss": "the passages sent to the model do not contain every key fact, so the answer "
                      "was never in front of the model",
    "no_passages": "no passage was retrieved",
    "model_abstained_with_evidence": "every key fact was in the passages but the model said it could "
                                     "not answer",
    "verifier_dropped_all_also_fails": "the verifier removed every claim, and the claims were wrong "
                                       "or incomplete anyway",
    "missing_key_facts": "answered from the right document but a key fact is missing from the answer",
    "abstained_other": "abstained for a reason not listed above",
}


OUTCOMES = {
    "answered_correctly": "answered, every key fact present",
    "answered_incorrectly": "answered, but a key fact is missing or a forbidden claim appears",
    "abstained_wrongly": "declined a question the documents can answer",
    "abstained_correctly": "declined a question the documents cannot answer",
    "answered_should_abstain": "answered a question the documents cannot answer",
    "error": "the call failed",
}


def outcome(row: dict) -> str:
    """What the user got for one question. Unlike pass/fail, this separates a wrong answer that was
    shown from a refusal, which is the trade a verifier makes."""
    answer, expect = row["answer"], row["q"]["expect"]
    if answer is None:
        return "error"
    if expect == "abstain":
        return "abstained_correctly" if row["ok"] else "answered_should_abstain"
    if answer.abstained:
        return "abstained_wrongly"
    return "answered_correctly" if row["ok"] else "answered_incorrectly"


def evidence_present(question: dict, passages: list[str]) -> bool:
    """Is every key fact of the question written in the given passages?

    This is a chunk-level check: a document can be retrieved while the one chunk that holds the
    answer is not. Questions without key facts fall back to the expected document being present.
    """
    text = fold(" ".join(passages))
    if question["key_facts"]:
        return all(fold(fact) in text for fact in question["key_facts"])
    return True


def classify(row: dict, off_row: dict | None) -> str | None:
    """The failure category of one result row, or None when the row passed.

    `off_row` is the same question asked with the verifier off. A failure the verifier causes is
    reported as such before anything else, because the fix is different from a retrieval or model fix.
    """
    if row["ok"]:
        return None
    answer, question = row["answer"], row["q"]
    if answer is None:
        return "error"
    if row["why"].startswith("forbidden claim"):
        return "forbidden_claim"
    if question["expect"] == "abstain":
        return "answered_should_abstain"
    if off_row is not None and off_row["ok"] and answer.dropped:
        return "verifier_false_drop"
    if not evidence_present(question, row.get("passages", [])):
        return "retrieval_miss"
    if answer.abstained:
        return {
            "no_passages": "no_passages",
            "model_found_no_answer": "model_abstained_with_evidence",
            "no_claim_survived_verification": "verifier_dropped_all_also_fails",
        }.get(answer.reason, "abstained_other")
    return "missing_key_facts"


def evidence_coverage(retriever, questions: list[dict], ks: tuple[int, ...]) -> dict[int, tuple[int, int]]:
    """For each k: how many answerable questions have every key fact in the top k passages.

    This is the ceiling of the whole system for a given k: a model cannot answer from a fact it was
    never shown. It uses the same hybrid search and passage format as the answer pipeline.
    """
    scored = [q for q in questions if q["expect"] == "answer" and q["key_facts"]]
    coverage = {}
    for k in ks:
        covered = 0
        for q in scored:
            hits = retriever.search(mask_pii(q["question"]).text, k=k)
            passages = [f"{h.chunk.heading}\n{h.chunk.text}" if h.chunk.heading else h.chunk.text
                        for h in hits]
            covered += evidence_present(q, passages)
        coverage[k] = (covered, len(scored))
    return coverage


def _short(text: str, limit: int = 150) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_failures(tag: str, model: str, rows: list[dict], off_rows: list[dict],
                    coverage: dict[int, tuple[int, int]] | None = None) -> str:
    off = {r["q"]["id"]: r for r in off_rows}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        category = classify(row, off.get(row["q"]["id"]))
        if category:
            grouped[category].append(row)
    failed = sum(len(v) for v in grouped.values())
    lines = [
        f"# Failure analysis - {tag} - {model} - verifier on",
        "",
        f"Questions: {len(rows)}. Failed: {failed}. Passed: {len(rows) - failed}.",
        "",
        "| Cause | Count | Meaning |",
        "|---|---|---|",
        *[f"| {c} | {len(grouped[c])} | {text} |" for c, text in CATEGORIES.items() if grouped[c]],
        "",
    ]
    if coverage:
        lines += [
            "## Ceiling: key facts present in the top-k passages",
            "",
            "Answerable questions whose every key fact is written in the k passages that hybrid search "
            "returns. The model cannot do better than this, whatever the prompt or verifier.",
            "",
            "| passages sent (k) | questions covered |",
            "|---|---|",
            *[f"| {k} | {c}/{n} |" for k, (c, n) in coverage.items()],
            "",
        ]
    for category, text in CATEGORIES.items():
        if not grouped[category]:
            continue
        lines += [f"## {category} ({len(grouped[category])})", "", text, ""]
        for row in grouped[category]:
            q, answer = row["q"], row["answer"]
            lines.append(f"- **{q['id']}** ({q['kind']}, expect={q['expect']}): {q['question']}")
            if answer is None:
                lines.append(f"  - {row['why']}")
                continue
            lines.append(f"  - answer: {_short(answer.answer)}")
            lines.append(f"  - why failed: {row['why']}; retrieved docs {answer.retrieved_docs}, "
                         f"expected {q['expected_docs']}")
            for verdict in answer.dropped:
                lines.append(f"  - verifier removed [{verdict.reason}]: claim \"{_short(verdict.claim.text, 110)}\""
                             f" quote \"{_short(verdict.claim.quote, 110)}\"")
        lines.append("")
    return "\n".join(lines)


def render_compare(tag: str, model: str, rows: list[dict], off_rows: list[dict]) -> str:
    off = {r["q"]["id"]: r for r in off_rows}
    helped = [r for r in rows if r["ok"] and not off[r["q"]["id"]]["ok"]]
    hurt = [r for r in rows if not r["ok"] and off[r["q"]["id"]]["ok"]]
    both_ok = sum(1 for r in rows if r["ok"] and off[r["q"]["id"]]["ok"])
    both_fail = sum(1 for r in rows if not r["ok"] and not off[r["q"]["id"]]["ok"])
    answered = [r for r in rows if r["answer"] is not None]
    kept = sum(len(r["answer"].citations) for r in answered)
    dropped = [v for r in answered for v in r["answer"].dropped]
    reasons = Counter(v.reason for v in dropped)
    on_outcomes, off_outcomes = Counter(map(outcome, rows)), Counter(map(outcome, off_rows))
    by_kind: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        bucket = by_kind[r["q"]["kind"]]
        bucket[0] += r["ok"]
        bucket[1] += off[r["q"]["id"]]["ok"]
        bucket[2] += 1
    lines = [
        f"# Verifier on versus off - {tag} - {model}",
        "",
        "Both runs judge the same recorded model replies, so the model is not called again.",
        "",
        "| | Passed |",
        "|---|---|",
        f"| verifier on | {sum(r['ok'] for r in rows)}/{len(rows)} |",
        f"| verifier off | {sum(r['ok'] for r in off_rows)}/{len(off_rows)} |",
        "",
        f"Question by question: {both_ok} pass either way, {both_fail} fail either way, "
        f"**{len(helped)} pass only with the verifier**, **{len(hurt)} pass only without it**.",
        "",
        f"Claims: the model produced {kept + len(dropped)}, the verifier kept {kept} and removed "
        f"{len(dropped)}. Removal reasons: "
        + (", ".join(f"{k} {v}" for k, v in reasons.most_common()) or "none") + ".",
        "",
        "What the user got:",
        "",
        "| Outcome | on | off | Meaning |",
        "|---|---|---|---|",
        *[f"| {name} | {on_outcomes[name]} | {off_outcomes[name]} | {text} |"
          for name, text in OUTCOMES.items() if on_outcomes[name] or off_outcomes[name]],
        "",
        "| Kind | on | off |",
        "|---|---|---|",
        *[f"| {k} | {v[0]}/{v[2]} | {v[1]}/{v[2]} |" for k, v in sorted(by_kind.items())],
        "",
        "## Passed only with the verifier (it caught something)",
        "",
    ]
    for r in helped:
        lines.append(f"- {r['q']['id']} ({r['q']['kind']}): {r['q']['question']}")
        off_answer = off[r["q"]["id"]]["answer"]
        lines.append(f"  - without verifier: {_short(off_answer.answer) if off_answer else r['why']}")
    if not helped:
        lines.append("- none")
    lines += ["", "## Passed only without the verifier (it removed something it should have kept)", ""]
    for r in hurt:
        lines.append(f"- {r['q']['id']} ({r['q']['kind']}): {r['q']['question']}")
        for verdict in r["answer"].dropped if r["answer"] else []:
            lines.append(f"  - removed [{verdict.reason}]: \"{_short(verdict.claim.text, 110)}\"")
    if not hurt:
        lines.append("- none")
    lines += ["", "## Every claim the verifier removed", "",
              "Listed so a person can judge each removal; the pass/fail numbers cannot.", ""]
    for r in answered:
        for verdict in r["answer"].dropped:
            lines.append(f"- {r['q']['id']} ({'passed' if r['ok'] else 'failed'}) [{verdict.reason}] "
                         f"claim \"{_short(verdict.claim.text, 120)}\" | quote \"{_short(verdict.claim.quote, 120)}\"")
    if not dropped:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="L0", choices=sorted(STAGES), help="a stage of eval.live")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="embedding model for retrieval")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    stage = STAGES[args.tag]
    chunks, questions = stage.loader()
    retriever = Retriever(chunks, args.model)
    on = run(build_llm("cached"), True, 0.0, retriever, questions, stage.top_k)
    off = run(build_llm("cached"), False, 0.0, retriever, questions, stage.top_k)
    coverage = evidence_coverage(retriever, questions, (3, 4, 5, 6, 8, 10))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / f"failures_{args.tag}.md").write_text(
        render_failures(args.tag, on["model"], on["rows"], off["rows"], coverage), encoding="utf-8")
    (args.out_dir / f"verify_compare_{args.tag}.md").write_text(
        render_compare(args.tag, on["model"], on["rows"], off["rows"]), encoding="utf-8")
    print(f"on {sum(r['ok'] for r in on['rows'])}/{len(questions)}, "
          f"off {sum(r['ok'] for r in off['rows'])}/{len(questions)}; cache misses {on['cache']['misses']}")
    print(f"written to {args.out_dir}")


if __name__ == "__main__":
    main()
