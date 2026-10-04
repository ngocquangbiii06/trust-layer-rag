"""Claim-level verification: a claim is kept only if the passage it cites supports it."""

import re
from dataclasses import dataclass

from app.text import fold, tokens

_NUMBER = re.compile(r"\d+(?:[.,]\d+)*%?")
_STOP = {
    "la", "va", "cua", "co", "khong", "duoc", "cho", "trong", "den", "tu", "mot", "cac", "nhung",
    "the", "thi", "se", "da", "bi", "khi", "neu", "de", "voi", "nay", "do", "o", "tren", "ve",
}


@dataclass(frozen=True)
class Claim:
    text: str
    source: int  # 1-based index of the passage the claim cites
    quote: str  # text the model says it copied from that passage


@dataclass(frozen=True)
class Verdict:
    claim: Claim
    ok: bool
    reason: str  # "" when ok


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _numbers(text: str) -> set[str]:
    return {re.sub(r"[.,]", "", n) for n in _NUMBER.findall(text)}


def _content_words(text: str) -> set[str]:
    return {t for t in tokens(text) if t not in _STOP and not t.isdigit()}


def verify_claim(
    claim: Claim, passages: list[str], question: str = "", min_overlap: float = 0.5
) -> Verdict:
    """Four checks, cheapest first. All must pass.

    1. The cited passage exists.
    2. The quote really appears in that passage (after whitespace and case folding).
    3. Every number in the claim is backed: it appears in the quote, or in the heading of the
       cited passage (a label such as "Cấp 2"), or in the question (the claim restates it).
       This catches invented figures.
    4. Enough of the claim's content words appear in the quote. This catches a true quote
       attached to a claim it does not support.
    """
    if not 1 <= claim.source <= len(passages):
        return Verdict(claim, False, "bad_source")
    passage = passages[claim.source - 1]
    quote = _squash(claim.quote)
    if len(quote) < 8 or fold(quote) not in fold(_squash(passage)):
        return Verdict(claim, False, "quote_not_in_source")
    heading = passage.split("\n", 1)[0] if "\n" in passage else ""
    if not _numbers(claim.text) <= (_numbers(quote) | _numbers(heading) | _numbers(question)):
        return Verdict(claim, False, "number_not_in_quote")
    words = _content_words(claim.text)
    if words:
        overlap = len(words & _content_words(quote)) / len(words)
        if overlap < min_overlap:
            return Verdict(claim, False, "claim_not_supported_by_quote")
    return Verdict(claim, True, "")


def verify_claims(claims: list[Claim], passages: list[str], question: str = "") -> list[Verdict]:
    return [verify_claim(c, passages, question) for c in claims]
