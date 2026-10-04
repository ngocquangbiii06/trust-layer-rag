"""Vietnamese text helpers: accent folding and tokenising."""

import re
import unicodedata

_NON_WORD = re.compile(r"[^0-9a-z]+")


def fold(text: str) -> str:
    """Lowercase and strip diacritics, so "Hạn mức" and "han muc" compare equal."""
    decomposed = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def tokens(text: str) -> list[str]:
    """Folded word tokens. Numbers such as 5.000.000 become one token: 5000000."""
    cleaned = re.sub(r"(?<=\d)[.,](?=\d{3}\b)", "", fold(text))
    return [t for t in _NON_WORD.split(cleaned) if t]


def terms(text: str) -> list[str]:
    """Unigrams plus bigrams. Vietnamese words are often two syllables ("tai khoan")."""
    words = tokens(text)
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:], strict=False)]
