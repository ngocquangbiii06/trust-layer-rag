"""End-to-end evaluation: question in, final answer out.

Usage:
  python -m eval.answer_eval --llm extractive            offline baseline, no key needed
  python -m eval.answer_eval --llm cached                replay replies recorded earlier, no key
  python -m eval.answer_eval --llm live --sleep 3        calls the model (GROQ_API_KEY), records replies
  add --no-verify to switch the claim verifier off (ablation)

`live` and `cached` read and write `eval/llm_cache/`, so a run with the verifier on and a run with
it off judge the very same model replies. `python -m eval.live` is the command that drives both.

Per question the check depends on `expect`:
  answer   the system answered, every key fact is in the answer, no forbidden claim appears
  abstain  the system declined and no forbidden claim appears
Also measured: raw personal data reaching the model, the audit log or the cache (must be 0), and
how many claims the verifier removed.
"""

import argparse
import json
import os
import re
import statistics
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import httpx

from app.answer import DEFAULT_TOP_K, AnswerService
from app.audit import AuditLog
from app.corpus import load_chunks
from app.llm import CachedLLM, ExtractiveLLM, LLMReply, OpenAICompatLLM
from app.retrieval import DEFAULT_MODEL, Retriever
from app.text import fold
from eval.retrieval_eval import load_questions

ROOT = Path(__file__).resolve().parent
CACHE_DIR = Path(os.getenv("LLM_CACHE_DIR") or ROOT / "llm_cache")  # the env var is for experiments


class SpyLLM:
    """Wraps a model and remembers everything it was sent and what it cost."""

    def __init__(self, inner) -> None:
        self.inner, self.name = inner, inner.name
        self.seen: list[str] = []
        self.passages: list[list[str]] = []  # the passages of each call, so failures can be traced
        self.model_latencies: list[int] = []
        self.tokens = {"prompt_tokens": 0, "completion_tokens": 0}

    def complete(self, question: str, passages: list[str]) -> LLMReply:
        self.seen.append(question + "\n" + "\n".join(passages))
        self.passages.append(passages)
        reply = self.inner.complete(question, passages)
        if reply.latency_ms:
            self.model_latencies.append(reply.latency_ms)
        for key in self.tokens:
            self.tokens[key] += reply.usage.get(key, 0)
        return reply


def build_llm(kind: str, cache_dir: Path = CACHE_DIR):
    if kind == "extractive":
        return ExtractiveLLM()
    return CachedLLM(OpenAICompatLLM(), cache_dir, "record" if kind == "live" else "replay")


def judge(question: dict, answer) -> tuple[bool, str]:
    text = fold(answer.answer)
    leaked = [f for f in question["forbidden_claims"] if fold(f) in text]
    if leaked:
        return False, f"forbidden claim present: {leaked}"
    if question["expect"] == "abstain":
        return (True, "") if answer.abstained else (False, "answered but should have abstained")
    if answer.abstained:
        return False, f"abstained ({answer.reason}) but should have answered"
    missing = [f for f in question["key_facts"] if fold(f) not in text]
    return (True, "") if not missing else (False, f"missing key facts: {missing}")


_SECRET = re.compile(r"(?:gsk_|sk-)[A-Za-z0-9_-]{8,}")


def describe_error(error: Exception) -> str:
    """One line saying why a call failed. For an HTTP error it includes the start of the response
    body, where the API explains itself. Anything shaped like an API key is blanked out."""
    text = str(error).splitlines()[0] if str(error) else type(error).__name__
    if isinstance(error, httpx.HTTPStatusError):
        body = " ".join(error.response.text.split())[:300]
        text = f"HTTP {error.response.status_code}: {body}"
    return _SECRET.sub("[REDACTED]", text)


def run(llm, verify: bool, sleep: float, retriever: Retriever, questions: list[dict] | None = None,
        top_k: int = DEFAULT_TOP_K) -> dict:
    """Ask every question. `sleep` seconds are waited after each question that really called a model."""
    questions = load_questions() if questions is None else questions
    cached = llm if isinstance(llm, CachedLLM) else None
    spy = SpyLLM(llm)
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "audit.jsonl"
        service = AnswerService(retriever, spy, AuditLog(log_path), top_k=top_k, verify=verify)
        rows = []
        for q in questions:
            start, live_before = len(spy.seen), cached.live_calls if cached else 0
            try:
                answer = service.ask(q["question"])
            except Exception as error:  # a failed live call must not hide the other results
                rows.append({"q": q, "ok": False, "why": f"error: {describe_error(error)}",
                             "answer": None, "sent": [],
                             "passages": [p for call in spy.passages[start:] for p in call]})
            else:
                ok, why = judge(q, answer)
                rows.append({"q": q, "ok": ok, "why": why, "answer": answer, "sent": spy.seen[start:],
                             "passages": [p for call in spy.passages[start:] for p in call]})
            if cached and cached.live_calls > live_before:
                time.sleep(sleep)
        log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    cache_text = "".join(p.read_text(encoding="utf-8") for p in cached.touched) if cached else ""
    pii_leaks = 0
    for row in rows:
        for value in row["q"]["pii"]:
            if value in log_text or value in cache_text or any(value in s for s in row["sent"]):
                pii_leaks += 1
    return {
        "rows": rows,
        "pii_leaks": pii_leaks,
        "model": spy.name,
        "verify": verify,
        "top_k": top_k,
        "cache": {"hits": cached.hits, "live_calls": cached.live_calls, "misses": cached.misses}
        if cached else None,
        "model_latencies": spy.model_latencies,
        "tokens": spy.tokens,
    }


def _median(values: list[int]) -> str:
    return f"{int(statistics.median(values))} ms" if values else "n/a"


def render(result: dict) -> str:
    rows = result["rows"]
    by_expect: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_kind: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in rows:
        for bucket, key in ((by_expect, r["q"]["expect"]), (by_kind, r["q"]["kind"])):
            bucket[key][0] += r["ok"]
            bucket[key][1] += 1
    answered = [r for r in rows if r["answer"] is not None]
    dropped = sum(len(r["answer"].dropped) for r in answered)
    pii_questions = sum(len(r["q"]["pii"]) for r in rows)
    cache = result["cache"]
    pipeline_latency = _median([r["answer"].latency_ms for r in answered])
    lines = [
        f"# End-to-end evaluation - {result['model']} - verifier {'on' if result['verify'] else 'OFF'}",
        "",
        f"Questions: {len(rows)}. Passed: {sum(r['ok'] for r in rows)}/{len(rows)}. "
        f"Passages sent to the model per question: {result['top_k']}.",
        "",
        "| Group | Passed |",
        "|---|---|",
        *[f"| expect={k} | {v[0]}/{v[1]} |" for k, v in sorted(by_expect.items())],
        *[f"| kind={k} | {v[0]}/{v[1]} |" for k, v in sorted(by_kind.items())],
        "",
        f"- Raw personal data reaching the model, the audit log or the cache: {result['pii_leaks']} of {pii_questions} values",
        f"- Claims removed by the verifier: {dropped}",
    ]
    if cache:
        lines += [
            f"- Model replies: {cache['hits']} from the cache, {cache['live_calls']} live calls, "
            f"{cache['misses']} missing (a missing reply shows as an error below)",
            f"- Median model latency, as recorded: {_median(result['model_latencies'])}",
            f"- Median pipeline latency: {pipeline_latency} (replayed replies cost no model time)",
            f"- Tokens, from the replies that reported them: {result['tokens']['prompt_tokens']} in, "
            f"{result['tokens']['completion_tokens']} out",
        ]
    else:
        lines.append(f"- Median latency: {pipeline_latency}")
    lines += ["", "## Failures", ""]
    failures = [r for r in rows if not r["ok"]]
    if not failures:
        lines.append("- none")
    for r in failures:
        text = r["answer"].answer if r["answer"] else "-"
        lines.append(f"- {r['q']['id']} ({r['q']['kind']}): {r['why']}. Q: {r['q']['question']} A: {text[:160]}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", choices=["extractive", "cached", "live"], default="extractive")
    parser.add_argument("--no-verify", action="store_true")
    parser.add_argument("--sleep", type=float, default=3.0)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="passages sent to the model")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    if args.llm == "live" and not OpenAICompatLLM.available():
        raise SystemExit("Set GROQ_API_KEY (or LLM_API_KEY) in the environment first.")
    retriever = Retriever(load_chunks(), args.model)
    report = render(run(build_llm(args.llm), not args.no_verify, args.sleep, retriever,
                        top_k=args.top_k))
    default = f"answers_{args.llm}{'_noverify' if args.no_verify else ''}.md"
    out = Path(args.out) if args.out else ROOT / "results" / default
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(json.dumps({"written": str(out)}))
    print(report)


if __name__ == "__main__":
    main()
