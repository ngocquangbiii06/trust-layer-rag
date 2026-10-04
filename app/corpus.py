"""Load the policy documents and turn them into chunks."""

from pathlib import Path

from app.chunking import Chunk, chunk_markdown

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "docs"


def load_chunks(docs_dir: Path = DOCS_DIR, max_chars: int = 600) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(docs_dir.glob("*.md")):
        doc_id = path.name.split("_", 1)[0]
        chunks.extend(chunk_markdown(doc_id, path.read_text(encoding="utf-8"), max_chars))
    return chunks


def doc_title(doc_id: str, docs_dir: Path = DOCS_DIR) -> str:
    for path in docs_dir.glob(f"{doc_id}_*.md"):
        first = path.read_text(encoding="utf-8").splitlines()[0]
        return first.lstrip("# ").strip()
    return doc_id
