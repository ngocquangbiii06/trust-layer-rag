# Verifier on versus off - L0c - openai-compat:openai/gpt-oss-20b

Both runs judge the same recorded model replies, so the model is not called again.

| | Passed |
|---|---|
| verifier on | 53/60 |
| verifier off | 53/60 |

Question by question: 53 pass either way, 7 fail either way, **0 pass only with the verifier**, **0 pass only without it**.

Claims: the model produced 52, the verifier kept 52 and removed 0. Removal reasons: none.

What the user got:

| Outcome | on | off | Meaning |
|---|---|---|---|
| answered_correctly | 42 | 42 | answered, every key fact present |
| answered_incorrectly | 4 | 4 | answered, but a key fact is missing or a forbidden claim appears |
| abstained_wrongly | 3 | 3 | declined a question the documents can answer |
| abstained_correctly | 11 | 11 | declined a question the documents cannot answer |

| Kind | on | off |
|---|---|---|
| ambiguous | 0/1 | 0/1 |
| injection | 2/2 | 2/2 |
| multi_doc | 2/3 | 2/3 |
| near_miss | 1/1 | 1/1 |
| no_diacritics | 1/2 | 1/2 |
| out_of_scope | 2/2 | 2/2 |
| paraphrase | 16/20 | 16/20 |
| pii | 2/2 | 2/2 |
| plain | 20/20 | 20/20 |
| unanswerable | 7/7 | 7/7 |

## Passed only with the verifier (it caught something)

- none

## Passed only without the verifier (it removed something it should have kept)

- none

## Every claim the verifier removed

Listed so a person can judge each removal; the pass/fail numbers cannot.

- none
