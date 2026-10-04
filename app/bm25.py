"""A small BM25 index over folded unigram and bigram terms."""

import math
from collections import Counter

from app.text import terms


class BM25:
    def __init__(self, documents: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self._tf = [Counter(terms(doc)) for doc in documents]
        self._len = [sum(tf.values()) for tf in self._tf]
        self._avg = (sum(self._len) / len(self._len)) if self._len else 0.0
        document_frequency: Counter[str] = Counter()
        for tf in self._tf:
            document_frequency.update(tf.keys())
        n = len(documents)
        self._idf = {
            term: math.log(1 + (n - df + 0.5) / (df + 0.5)) for term, df in document_frequency.items()
        }

    def scores(self, query: str) -> list[float]:
        query_terms = set(terms(query))
        result = []
        for tf, length in zip(self._tf, self._len, strict=True):
            score = 0.0
            for term in query_terms:
                frequency = tf.get(term, 0)
                if not frequency:
                    continue
                norm = frequency + self.k1 * (1 - self.b + self.b * length / (self._avg or 1))
                score += self._idf[term] * frequency * (self.k1 + 1) / norm
            result.append(score)
        return result

    def top(self, query: str, k: int) -> list[tuple[int, float]]:
        ranked = sorted(enumerate(self.scores(query)), key=lambda pair: pair[1], reverse=True)
        return [(i, s) for i, s in ranked[:k] if s > 0]
