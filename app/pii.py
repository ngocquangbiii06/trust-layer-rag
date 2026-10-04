"""Mask personal data before it reaches a model or a log."""

import re
from dataclasses import dataclass


def _joined(layouts: list[tuple[int, ...]], sep: str, zero: bool = False) -> str:
    """Regex for digit groups of the given sizes joined by `sep`; (4, 3, 3) matches 0912 345 678.

    With `zero` the first group must start with 0, as Vietnamese phone numbers do.
    """
    alternatives = []
    for layout in layouts:
        groups = [rf"\d{{{n}}}" for n in layout]
        if zero:
            groups[0] = rf"0\d{{{layout[0] - 1}}}"
        alternatives.append(sep.join(groups))
    return "|".join(alternatives)


# A dot is also the thousands separator (5.000.000, 300.000.000.000), so a dotted number counts as
# personal data only when its shape cannot be money: a phone number that starts with 0 or +84.
# CCCD and account numbers are matched with spaces or dashes only.
_ANY_SEP, _NO_DOT = r"[ .-]", r"[ -]"
_PHONE = [(4, 3, 3), (3, 3, 4), (3, 4, 3), (4, 6), (3, 7)]  # ten digits, the leading 0 included
_PHONE_INTL = [(3, 3, 3), (2, 3, 4), (2, 4, 3), (3, 6), (2, 7)]  # the nine digits after +84
_CCCD = [(3, 3, 3, 3), (4, 4, 4), (6, 6)]

# Order matters: a pattern that runs first claims its text. The 4-4-4-4 card shape must run before
# CCCD, or "1234 5678 9012" would be taken as a CCCD and leave " 3456" behind.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("SO_TAI_KHOAN", re.compile(r"(?<!\d)\d{4}(?:[ -]\d{4}){2}[ -]\d{1,4}(?!\d)")),
    ("CCCD", re.compile(rf"(?<!\d)(?:\d{{12}}|{_joined(_CCCD, _NO_DOT)})(?!\d)")),
    (
        "SDT",
        re.compile(
            r"(?<!\d)(?:\+?84|0)\d{9}(?!\d)"
            rf"|(?<![\d+])(?:{_joined(_PHONE, _ANY_SEP, zero=True)})(?!\d)"
            rf"|(?<![\d+])(?:\(\+84\)|\+84){_ANY_SEP}?(?:{_joined(_PHONE_INTL, _ANY_SEP)})(?!\d)"
            rf"|(?<![\d+])84{_NO_DOT}?(?:{_joined(_PHONE_INTL, _NO_DOT)})(?!\d)"
        ),
    ),
    ("SO_TAI_KHOAN", re.compile(r"(?<!\d)\d{9,16}(?!\d)")),
]


@dataclass(frozen=True)
class Masked:
    text: str
    types: tuple[str, ...]  # which kinds of data were found, in order of appearance


def mask_pii(text: str) -> Masked:
    found: list[tuple[int, str]] = []
    result = text
    for kind, pattern in _PATTERNS:
        def replace(match: re.Match[str], kind: str = kind) -> str:
            found.append((match.start(), kind))
            return f"[{kind}]"

        result = pattern.sub(replace, result)
    found.sort()
    return Masked(result, tuple(dict.fromkeys(kind for _, kind in found)))
