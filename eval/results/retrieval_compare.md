# Retrieval configurations compared (hybrid search, no language model)

evidence@k: every key fact of the question is in the top k chunks.

| Config | doc@1 | doc@3 | evidence@3 | evidence@4 | evidence@6 | ms per query |
|---|---|---|---|---|---|---|
| minilm | 33/49 | 43/49 | 36/49 | 38/49 | 44/49 | 17 |
| mpnet | 39/49 | 47/49 | 41/49 | 43/49 | 45/49 | 22 |
| e5-large | 41/49 | 46/49 | 42/49 | 43/49 | 46/49 | 555 |
| minilm+rerank | 41/49 | 47/49 | 44/49 | 45/49 | 46/49 | 4031 |
| mpnet+rerank | 43/49 | 47/49 | 46/49 | 46/49 | 47/49 | 4635 |
| e5-large+rerank | 41/49 | 47/49 | 45/49 | 46/49 | 47/49 | 5668 |
