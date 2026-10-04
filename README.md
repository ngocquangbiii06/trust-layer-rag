# Trust-layer RAG

Vietnamese question answering over policy documents, built around one idea: **do not trust the
language model, check it.** Every answer is a list of short claims, each claim must quote the
passage it came from, and a verifier throws away any claim that the quoted passage does not support.
If nothing survives, the system says it has no basis to answer instead of guessing. Personal data in
a question is masked before it reaches search, the model or the audit log. An evaluation harness
measures all of this.

> **Work in progress, and the data is fictional.** The corpus is 12 synthetic policy documents of an
> invented e-wallet ("Ví Mây"). Nothing here is the policy of a real company and nothing here claims
> legal or regulatory compliance. See [Limitations](#limitations) before reading any number.

## How a question flows

```
question
  └─► mask personal data  ([SDT] [CCCD] [EMAIL] [SO_TAI_KHOAN])
        └─► hybrid retrieval: BM25 on accent-folded text  +  multilingual vectors (Qdrant)
              fused with Reciprocal Rank Fusion
              └─► LLM returns {answerable, claims[{text, source, quote}]}  (strict JSON schema)
                    └─► claim verifier ── every claim must pass 4 checks
                          ├─ at least one claim survives ─► answer with numbered citations
                          └─ none survives ───────────────► "no basis found" (abstain)
every request ─► append-only audit log (masked text only)
```

Components, in the order a question meets them:

| Step | Code | What it does |
|---|---|---|
| Chunking | `app/chunking.py` | Splits Markdown by heading; each chunk keeps its heading; long sections split by paragraph, sentence, then word. |
| Text normalisation | `app/text.py` | Lower-cases and strips diacritics so "Hạn mức" and "han muc" match; keeps `5.000.000` as one token; adds bigrams. |
| Sparse search | `app/bm25.py` | BM25 written from scratch. |
| Dense search | `app/retrieval.py` | `paraphrase-multilingual-MiniLM-L12-v2` (ONNX, via fastembed) in an in-memory Qdrant collection. |
| Fusion | `app/fusion.py` | Reciprocal Rank Fusion: scores of BM25 and vectors are not comparable, ranks are. |
| Masking | `app/pii.py` | Regex masking of phone numbers, national ID (CCCD), emails and account numbers, including grouped forms such as `0912 345 678`. |
| Model interface | `app/llm.py` | Any OpenAI-compatible API (Groq by default) with a strict JSON schema, plus an offline baseline that needs no model. Replies are cached on disk so evaluations can be replayed without a key. |
| Verifier | `app/verify.py` | See below. |
| Pipeline | `app/answer.py` | mask → retrieve → generate → verify → answer or abstain → audit. |
| Service | `app/main.py` | FastAPI: `POST /ask`, `POST /search`, `GET /health`, and a small web page at `/`. |

### The verifier

A claim is kept only if all four checks pass:

1. The passage it cites exists.
2. Its quote really appears in that passage (after whitespace and accent folding).
3. Every number in the claim is backed by the quote, the passage heading or the question. This
   catches invented figures.
4. At least half of the claim's content words appear in the quote. This catches a true quote
   attached to a claim it does not support.

It is a set of rules, not a second model. It does not detect a claim that reverses the meaning of
its quote ("allowed" vs "not allowed"); that is a known gap.

## Results

Every number below is produced by a command in [Reproduce](#reproduce) and the output is stored in
`eval/results/`. 60 hand-written questions over 12 documents (49 chunks): plain, paraphrased,
unanswerable, near-miss, out of scope, prompt injection, personal data, no diacritics.

### Retrieval: does the right document appear in the top k chunks?

49 questions that have an answer. `any@k`: at least one expected document is among the top k chunks.
Embedding model: `paraphrase-multilingual-MiniLM-L12-v2`.

| Mode | any@1 | any@3 | any@5 |
|---|---|---|---|
| dense (vectors only) | 30/49 | 39/49 | 41/49 |
| BM25 only | 32/49 | 45/49 | 45/49 |
| hybrid (BM25 + vectors, RRF) | 33/49 | 43/49 | 47/49 |

Source: [`eval/results/retrieval_paraphrase-multilingual-MiniLM-L12-v2.md`](eval/results/retrieval_paraphrase-multilingual-MiniLM-L12-v2.md).
BM25 is best at k=3 and hybrid is best at k=5. The small embedding model is weaker than BM25 on this
set; larger embedding models have not been compared yet.

### End to end, offline baseline (no language model)

`ExtractiveLLM` copies the best-matching sentence. It exists to show what a model and the verifier
add, and to keep the whole pipeline runnable without a key.

| Group | Passed |
|---|---|
| all questions | 23/60 |
| paraphrased questions | 3/20 |
| questions with personal data | 0/2 |

Raw personal data reaching the model or the audit log: **0 of 2** values.
Source: [`eval/results/answers_extractive.md`](eval/results/answers_extractive.md).

### End to end, live language model

`openai/gpt-oss-20b` through Groq, temperature 0, 4 passages per question (the default). Verifier on
and off judge the same recorded replies, so the difference is caused by the verifier alone.

| | verifier on | verifier off |
|---|---|---|
| **questions passed** | **48/60** | **49/60** |
| answered correctly | 38 | 39 |
| answered, but a key fact is missing | 3 | 4 |
| declined a question the documents can answer | 8 | 6 |
| declined a question the documents cannot answer (correct) | 10/11 | 10/11 |
| call failed | 1 | 1 |

By group, verifier on: plain 20/20, paraphrased 11/20, unanswerable 7/7, out of scope 2/2,
multi-document 3/3, personal data 2/2, prompt injection 1/2, no diacritics 1/2.
Raw personal data reaching the model, the audit log or the reply cache: **0 of 2** values.
Median model latency 1.9 s. Sources: [`answers_live_L0.md`](eval/results/answers_live_L0.md),
[`answers_live_L0_noverify.md`](eval/results/answers_live_L0_noverify.md),
[`verify_compare_L0.md`](eval/results/verify_compare_L0.md).

**What the numbers say, including the unflattering parts:**

- **The model adds a lot** over the no-model baseline: 48/60 against 23/60.
- **The verifier did not raise the pass count here.** It removed 4 of 51 claims. Reading them by
  hand (one reader, not a labelled set): 1 was a wrong claim built on an unrelated quote, 3 were
  reasonable paraphrases. The word-overlap rule punishes paraphrase. Its real effect is to turn a
  shown answer into a refusal: one fewer incomplete answer shown, two more wrong refusals.
- **Retrieval is the bottleneck, not the model.** Of the 12 failures, 10 are questions where the
  chunk holding the answer was not among the 4 passages sent to the model, so declining was the
  right behaviour. The key facts are present in the top 4 passages for only 39 of 49 answerable
  questions; that is the ceiling for any prompt. See [`failures_L0.md`](eval/results/failures_L0.md).
- **One prompt-injection question ends in an error, not a clean refusal.** The model refused in
  plain text, the API rejected that as invalid JSON, and the pipeline raised an error. Nothing
  leaked, but it is counted as a failure and the pipeline should fail closed instead.

### One tuning round, and it did not help

Because the ceiling rises to 44/49 with 6 passages, the single change tried was sending 6 passages
instead of 4. The decision rule was written down before the run: keep 6 only if it passes more
questions with the verifier on.

| passages per question | verifier on | verifier off | no-model baseline |
|---|---|---|---|
| 4 (kept as default) | 48/60 | 49/60 | 23/60 |
| 6 | 45/60 | 48/60 | 22/60 |

More passages put the answer in front of the model more often (retrieval misses fell from 10 to
5), but the model also answered one unanswerable question, and the verifier wrongly removed more
claims (3 questions pass only with the verifier off). Four of those removals were quotes the model
copied correctly except for quote marks or a line break, which the exact-match check rejects: a
verifier bug found by this run and not yet fixed. Sources:
[`answers_live_L0b.md`](eval/results/answers_live_L0b.md),
[`failures_L0b.md`](eval/results/failures_L0b.md),
[`verify_compare_L0b.md`](eval/results/verify_compare_L0b.md).

## Limitations

- **The data is fictional.** 12 invented documents. Results say nothing about real policies.
- **Tuning and scoring use the same 60 questions.** There is no held-out set for this corpus, and
  the one tuning round above was chosen and judged on these same questions, so the numbers are
  optimistic. Scoring is by key-fact matching, which cannot tell whether an answer is otherwise right. Documents, questions and expected answers were drafted by a single source
  with AI assistance and have not been independently reviewed. The first 35 questions reused the
  documents' own wording and made keyword search look better than it is; the other 25 were added to
  expose that.
- **Small sample.** 60 questions, 49 of them answerable; one question is 1.7 percentage points.
- **Personal-data masking is regex-based.** It does not catch names or addresses, numbers of 17 or
  more digits, landline numbers, or unusual spellings of phone numbers.
- **The verifier is rule-based.** It checks quotes, numbers and word overlap, not meaning. On the
  live run it rejected correct paraphrases and correctly copied quotes that differed only in quote
  marks or line breaks, and it does not detect negation.
- **One model, one run.** A single 20B open-weight model at temperature 0; no repeat runs.
- **Retrieval has only been tried with the smallest embedding model**, and no reranker.
- **A legal-document corpus is in progress** (the 2025 Personal Data Protection Law and the
  consolidated State Bank circular on payment intermediary services, chunked by Article and Clause).
  None of the numbers above use it.
- **The code was written with heavy AI assistance (Claude).**

## Run

Python 3.12. The first run downloads the embedding model (about 220 MB).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest ruff
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload     # http://127.0.0.1:8000
```

Without an API key the offline baseline answers. To use a real model, set the key in your own shell
(never in a file) before starting the server:

```powershell
$env:GROQ_API_KEY = "<your key>"          # or LLM_API_KEY with LLM_BASE_URL / LLM_MODEL
```

A container build and a GitHub Actions workflow (lint, tests, offline evaluation, container smoke
test) are included.

## Reproduce

```powershell
python -m eval.retrieval_eval                    # retrieval table above
python -m eval.answer_eval --llm extractive      # offline baseline table above
python -m eval.answer_eval --llm cached          # replay recorded model replies, no key needed
python -m eval.live --stage L0                   # 4 passages; replays the recorded replies, no key needed
python -m eval.live --stage L0b                  # 6 passages (the tuning round)
python -m eval.failures --tag L0                 # group failures by cause, compare verifier on/off
```

`eval/live.py` records every model reply under `eval/llm_cache/`, so the verifier-on and verifier-off
reports judge exactly the same replies.

## Layout

```
app/        pipeline, retrieval, verifier, masking, API, web page
data/docs/  the 12 synthetic policy documents
eval/       questions.jsonl, evaluation scripts, results/, llm_cache/
tests/      unit tests
```
