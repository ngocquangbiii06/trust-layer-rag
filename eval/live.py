"""Evaluations that call a real model. They need an API key in the environment of the process.

In your own PowerShell, set the key for that window only, then run a stage:

  $env:GROQ_API_KEY = "<your key>"
  .\\.venv\\Scripts\\python.exe -m eval.live --stage L0

The command first replays what is already in `eval/llm_cache/` and counts the questions that have no
recorded reply. It calls the model only for those, records the replies, then writes two reports from
the cache: verifier on and verifier off. Running it again is safe: finished questions are not asked
again, and with nothing missing it needs no key at all. `--dry-run` only prints the count.
Calls that failed are listed in `eval/results/live_errors_<stage>.md`.
"""

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.corpus import load_chunks
from app.llm import OpenAICompatLLM
from app.retrieval import DEFAULT_MODEL, Retriever
from eval.answer_eval import build_llm, render, run
from eval.retrieval_eval import load_questions

ROOT = Path(__file__).resolve().parent
KEY_HELP = (
    "No API key found, and this stage has questions without a recorded reply.\n"
    "In YOUR PowerShell window (never paste the key into a chat, a file or a commit) run:\n"
    '  $env:GROQ_API_KEY = "<your key>"\n'
    "then run this command again."
)


@dataclass(frozen=True)
class Stage:
    label: str
    loader: Callable[[], tuple[list, list[dict]]]  # returns the chunks and the questions
    top_k: int  # passages sent to the model per question


def _vimay() -> tuple[list, list[dict]]:
    return load_chunks(), load_questions()


# Later work packages register L1 (legal dev set), L2 (attacks, judge) and L3 (held-out set) here.
STAGES: dict[str, Stage] = {
    "L0": Stage("60 questions about the fictional Vi May policies, 4 passages per question", _vimay, 4),
    "L0b": Stage("the same 60 questions, 6 passages per question (the one tuning round)", _vimay, 6),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--stage", choices=sorted(STAGES), required=True)
    parser.add_argument("--sleep", type=float, default=3.0, help="seconds to wait after each live call")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="embedding model for retrieval")
    parser.add_argument("--dry-run", action="store_true", help="count the missing replies and stop")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    stage = STAGES[args.stage]
    chunks, questions = stage.loader()
    retriever = Retriever(chunks, args.model)

    probe = run(build_llm("cached"), True, 0.0, retriever, questions, stage.top_k)
    missing = probe["cache"]["misses"]
    print(f"Stage {args.stage}: {stage.label}. Model: {OpenAICompatLLM().model}.")
    print(f"{missing} of {len(questions)} questions need a live call; the others are already "
          "recorded (or need no model call).")
    if args.dry_run:
        return
    args.results_dir.mkdir(parents=True, exist_ok=True)
    errors_path = args.results_dir / f"live_errors_{args.stage}.md"
    if missing:
        if not OpenAICompatLLM.available():
            raise SystemExit(KEY_HELP)
        print(f"Calling the model {missing} times, about {args.sleep:.0f}s apart. Ctrl+C is safe: "
              "replies are saved as they arrive.")
        recorded = run(build_llm("live"), True, args.sleep, retriever, questions, stage.top_k)
        errors = [f"- {r['q']['id']} ({r['q']['kind']}): {r['why']}" for r in recorded["rows"]
                  if r["answer"] is None]
        if errors:
            errors_path.write_text(f"# Failed live calls - stage {args.stage}\n\n" + "\n".join(errors) + "\n",
                                   encoding="utf-8")
        elif errors_path.exists():
            errors_path.unlink()

    for verify in (True, False):
        result = run(build_llm("cached"), verify, 0.0, retriever, questions, stage.top_k)
        name = f"answers_live_{args.stage}{'' if verify else '_noverify'}.md"
        (args.results_dir / name).write_text(render(result), encoding="utf-8")
        passed = sum(r["ok"] for r in result["rows"])
        print(f"verifier {'on ' if verify else 'OFF'}: {passed}/{len(questions)} passed -> {args.results_dir / name}")
    if result["cache"]["misses"]:
        print(f"{result['cache']['misses']} questions still have no reply (the calls failed, see "
              f"{errors_path.name}). Run this command again to retry only those.", file=sys.stderr)


if __name__ == "__main__":
    main()
