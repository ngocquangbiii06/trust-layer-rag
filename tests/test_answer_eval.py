import httpx

from app.chunking import Chunk
from app.llm import ExtractiveLLM
from app.retrieval import Hit
from eval.answer_eval import describe_error, render, run
from eval.live import STAGES

QUESTION = {"id": "Q01", "question": "Tổng giao dịch mỗi ngày của tài khoản cấp 1?", "kind": "plain",
            "expect": "answer", "expected_docs": ["01"], "key_facts": ["5.000.000"],
            "forbidden_claims": [], "pii": []}


class RecordingSearcher:
    def __init__(self) -> None:
        self.ks: list[int] = []

    def search(self, query, k=5, mode="hybrid"):
        self.ks.append(k)
        return [Hit(0, Chunk("01", "Cấp 1", "Tổng giao dịch mỗi ngày: 5.000.000 đồng."), 1.0, 1)]


def test_run_sends_the_requested_number_of_passages_and_reports_it():
    searcher = RecordingSearcher()
    result = run(ExtractiveLLM(), True, 0.0, searcher, [QUESTION], top_k=6)
    assert searcher.ks == [6] and result["top_k"] == 6
    assert result["rows"][0]["ok"] and result["rows"][0]["passages"] == ["Cấp 1\nTổng giao dịch mỗi ngày: 5.000.000 đồng."]
    assert "Passages sent to the model per question: 6" in render(result)


def test_the_two_vi_may_stages_differ_only_in_the_number_of_passages():
    assert (STAGES["L0"].top_k, STAGES["L0b"].top_k) == (4, 6)
    assert STAGES["L0"].loader is STAGES["L0b"].loader


def test_http_errors_are_described_with_the_body_and_without_secrets():
    request = httpx.Request("POST", "https://example.test/chat/completions")
    fake = "gsk_" + "fake_key_" * 3  # built here so no key-shaped literal sits in the repository
    body = {"error": {"code": "json_validate_failed", "failed_generation": f"key {fake} here"}}
    error = httpx.HTTPStatusError("boom", request=request, response=httpx.Response(400, json=body, request=request))
    text = describe_error(error)
    assert text.startswith("HTTP 400:") and "json_validate_failed" in text
    assert fake not in text and "[REDACTED]" in text


def test_other_errors_are_described_by_their_first_line():
    assert describe_error(RuntimeError("no recorded reply\nsecond line")) == "no recorded reply"
    assert describe_error(ValueError()) == "ValueError"
