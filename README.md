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

`openai/gpt-oss-20b` through Groq, temperature 0, 4 passages per question. Verifier on and off judge
the same recorded replies, so any difference is caused by the verifier alone.

| Retrieval configuration | verifier on | verifier off | ceiling* |
|---|---|---|---|
| A. MiniLM embeddings, 4 passages (first version, small and fast) | 49/60 | 50/60 | 38/49 |
| B. MiniLM embeddings, 6 passages | 48/60 | 49/60 | 44/49 |
| **C. mpnet embeddings + cross-encoder reranker, 4 passages** | **53/60** | **53/60** | 46/49 |
| no language model (extractive baseline, configuration A) | 23/60 | | |

\* ceiling: answerable questions whose every key fact is written in the passages sent to the model.
No prompt or verifier can beat it. Measured offline, see
[`retrieval_compare.md`](eval/results/retrieval_compare.md).

Configuration C by group (verifier on): plain 20/20, paraphrased 16/20, unanswerable 7/7, out of
scope 2/2, prompt injection 2/2, personal data 2/2, multi-document 2/3, no diacritics 1/2,
ambiguous 0/1. It declined all 11 questions that have no answer in the documents.
Raw personal data reaching the model, the audit log or the reply cache: **0 of 2** values, in every run.
Sources: `eval/results/answers_live_L0.md` (A), `answers_live_L0b.md` (B), `answers_live_L0c.md` (C),
each with a `_noverify` twin, plus `failures_*.md` and `verify_compare_*.md`.

**What the numbers say, including the unflattering parts:**

- **Retrieval was the bottleneck, not the model.** In configuration A, 10 of the 11 failures were
  questions where the chunk holding the answer was not among the 4 passages sent to the model, so
  declining was the right behaviour. That finding is what pointed to the fix.
- **Sending more passages did not help (B).** The ceiling rose but the model answered one
  unanswerable question and the verifier removed more correct claims.
- **A better embedding model plus a reranker did (C)**: the right chunk reaches the top 4 far more
  often, and the pass count went from 49 to 53. The cost is latency: about 5 s per question for
  retrieval and reranking on a laptop CPU, against about 20 ms for A.
- **The verifier has not shown a benefit on this set.** In A it removed 3 of 51 claims: one was a
  wrong claim built on an unrelated quote, two were reasonable paraphrases (one reader's judgement,
  not a labelled set). In C it removed nothing, so on and off agree. It guards against a failure
  this small model rarely produced here; its value is unproven until there is a harder test set.
- **Two of C's seven failures are right answers that the scorer rejects**: "không có cam kết" where
  the expected string is "không cam kết", and "không có phí duy trì" for "không thu phí". The
  labels were left as they are.
- **This run found three bugs, now fixed**: the verifier rejected correctly copied quotes that
  differed in quote marks or list bullets; it ignored the section heading as support; and a model
  refusing a prompt injection in plain text surfaced as an HTTP error instead of a clean refusal.
  The numbers above are after those fixes; the same recorded replies were re-judged.

The default configuration of the service and of the container stays A, because C needs 2 GB of
extra models and seconds per query. C is selected by passing the two model names to `Retriever`.

## Limitations

- **The data is fictional.** 12 invented documents. Results say nothing about real policies.
- **Tuning and scoring use the same 60 questions.** There is no held-out set for this corpus.
  Configurations B and C and the verifier fixes were all chosen and judged on these same questions,
  so 53/60 is optimistic. Scoring is by key-fact matching, which cannot tell whether an answer is otherwise right. Documents, questions and expected answers were drafted by a single source
  with AI assistance and have not been independently reviewed. The first 35 questions reused the
  documents' own wording and made keyword search look better than it is; the other 25 were added to
  expose that.
- **Small sample.** 60 questions, 49 of them answerable; one question is 1.7 percentage points.
- **Personal-data masking is regex-based.** It does not catch names or addresses, numbers of 17 or
  more digits, landline numbers, or unusual spellings of phone numbers.
- **The verifier is rule-based.** It checks quotes, numbers and word overlap, not meaning. It can
  reject a correct paraphrase and it does not detect negation.
- **One model, one run.** A single 20B open-weight model at temperature 0; no repeat runs.
- **The reranker model (`jinaai/jina-reranker-v2-base-multilingual`) is licensed CC BY-NC 4.0**,
  non-commercial use only.
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
python -m eval.live --stage L0b                  # configuration B
python -m eval.live --stage L0c                  # configuration C (downloads about 2 GB of models)
python -m eval.retrieval_compare                 # six retrieval configurations, no language model
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
