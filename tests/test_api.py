from fastapi.testclient import TestClient

import app.main as main
from app.answer import AnswerService
from app.chunking import Chunk
from app.llm import ExtractiveLLM
from app.retrieval import Hit


class StubSearcher:
    def search(self, query, k=5, mode="hybrid"):
        chunk = Chunk("05", "Khóa tạm thời do nhập sai mã PIN", "Nhập sai mã PIN 5 lần liên tiếp, tài khoản bị khóa tạm thời.")
        return [Hit(0, chunk, 1.0, 1)]


def client_with_stub(monkeypatch):
    stub_service = AnswerService(StubSearcher(), ExtractiveLLM())
    monkeypatch.setattr(main, "service", lambda: stub_service)
    monkeypatch.setattr(main, "retriever", lambda: StubSearcher())
    return TestClient(main.app)


def test_ask_returns_cited_answer(monkeypatch):
    response = client_with_stub(monkeypatch).post("/ask", json={"question": "Nhập sai mã PIN mấy lần thì bị khóa?"})
    body = response.json()
    assert response.status_code == 200 and not body["abstained"]
    assert body["citations"][0]["doc_id"] == "05"


def test_ask_masks_personal_data_in_the_response(monkeypatch):
    response = client_with_stub(monkeypatch).post("/ask", json={"question": "SĐT 0912345678 nhập sai mã PIN mấy lần bị khóa?"})
    body = response.json()
    assert "0912345678" not in str(body) and body["pii_types"] == ["SDT"]


def test_ask_rejects_too_short_questions(monkeypatch):
    assert client_with_stub(monkeypatch).post("/ask", json={"question": "a"}).status_code == 422


def test_search_rejects_unknown_mode(monkeypatch):
    response = client_with_stub(monkeypatch).post("/search?mode=magic", json={"question": "hạn mức"})
    assert response.status_code == 422


def test_home_page_is_served():
    response = TestClient(main.app).get("/")
    assert response.status_code == 200 and "Trợ lý chính sách" in response.text
