"""Reciprocal rank fusion: merge several ranked lists without comparing their raw scores."""


def rrf(rankings: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    """Each ranking is a list of item ids, best first. An item scores 1 / (k + rank) in every list
    that contains it (rank starts at 1). Return (id, score) sorted by score, best first."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for position, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + position)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
