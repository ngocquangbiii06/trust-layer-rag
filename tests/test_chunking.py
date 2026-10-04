"""Behaviour of chunk_markdown."""

from app.chunking import chunk_markdown

SHORT = """# Biểu phí

## Chuyển tiền
Chuyển ví sang ví miễn phí.

## Rút tiền
Phí 0,1% mỗi giao dịch.
"""


def test_empty_text_gives_no_chunks():
    assert chunk_markdown("00", "") == []
    assert chunk_markdown("00", "   \n\n ") == []


def test_one_chunk_per_short_section_with_its_heading():
    chunks = chunk_markdown("02", SHORT)
    assert [c.heading for c in chunks] == ["Chuyển tiền", "Rút tiền"]
    assert all(c.doc_id == "02" for c in chunks)
    assert "miễn phí" in chunks[0].text and "0,1%" in chunks[1].text


def test_no_chunk_is_empty():
    assert all(c.text.strip() for c in chunk_markdown("02", SHORT))


def test_long_section_is_split_and_each_chunk_fits():
    sentence = "Đây là một câu dài về chính sách của ví. "
    text = "## Mục dài\n" + sentence * 40
    chunks = chunk_markdown("99", text, max_chars=200)
    assert len(chunks) > 1
    assert all(len(c.text) <= 200 for c in chunks)
    assert all(c.heading == "Mục dài" for c in chunks)


def test_splitting_loses_no_words():
    sentence = "Hạn mức mỗi ngày được tính theo giờ Việt Nam. "
    text = "## Lưu ý\n" + sentence * 30
    chunks = chunk_markdown("01", text, max_chars=180)
    original = text.split("\n", 1)[1].split()
    rebuilt = " ".join(c.text for c in chunks).split()
    assert rebuilt == original
