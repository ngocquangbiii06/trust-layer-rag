"""Split a markdown policy document into chunks for retrieval.

A chunk keeps the heading of the section it came from. A section that fits in `max_chars` becomes
one chunk; a longer one is packed from paragraphs, then sentences, then words, so that no chunk is
longer than `max_chars` and no word is lost.
"""

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_SENTENCE_END = re.compile(r"(?<=[.!?;])\s+")


@dataclass(frozen=True)
class Chunk:
    doc_id: str  # e.g. "01" from the file name 01_han_muc_giao_dich.md
    heading: str  # the closest heading above the text, without the leading '#'
    text: str  # chunk body, at most `max_chars` characters


def _sections(markdown: str) -> list[tuple[str, str]]:
    """Return (heading, body) pairs. Text before the first heading has an empty heading."""
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in markdown.splitlines():
        match = _HEADING.match(line)
        if match:
            sections.append((match.group(2), []))
        else:
            sections[-1][1].append(line)
    return [(heading, "\n".join(lines).strip()) for heading, lines in sections]


def _split_words(text: str, max_chars: int) -> list[str]:
    pieces, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                pieces.append(current)
            while len(word) > max_chars:  # a single token longer than the limit
                pieces.append(word[:max_chars])
                word = word[max_chars:]
            current = word
    if current:
        pieces.append(current)
    return pieces


def _units(body: str, max_chars: int) -> list[str]:
    """Break a body into pieces that each fit, preferring paragraph and sentence boundaries."""
    units: list[str] = []
    for paragraph in re.split(r"\n\s*\n", body):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) <= max_chars:
            units.append(paragraph)
            continue
        for line in paragraph.splitlines():  # list items stay whole when they fit
            line = line.strip()
            if not line:
                continue
            if len(line) <= max_chars:
                units.append(line)
                continue
            for sentence in _SENTENCE_END.split(line):
                sentence = sentence.strip()
                if not sentence:
                    continue
                if len(sentence) <= max_chars:
                    units.append(sentence)
                else:
                    units.extend(_split_words(sentence, max_chars))
    return units


def chunk_markdown(doc_id: str, markdown: str, max_chars: int = 600) -> list[Chunk]:
    """Return the chunks of one document, in reading order."""
    if max_chars < 20:
        raise ValueError("max_chars is too small to hold a sentence")
    chunks: list[Chunk] = []
    for heading, body in _sections(markdown):
        if not body:
            continue
        if len(body) <= max_chars:
            chunks.append(Chunk(doc_id, heading, body))
            continue
        current = ""
        for unit in _units(body, max_chars):
            candidate = f"{current} {unit}".strip() if current else unit
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(Chunk(doc_id, heading, current))
                current = unit
        if current:
            chunks.append(Chunk(doc_id, heading, current))
    return chunks
