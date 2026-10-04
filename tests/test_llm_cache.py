import json

import httpx
import pytest

import app.llm as llm_module
from app.llm import CachedLLM, CacheMiss, LLMReply, OpenAICompatLLM, cache_key
from app.verify import Claim

PASSAGES = ["Cấp 1\nTổng giao dịch mỗi ngày: 5.000.000 đồng."]
REPLY = LLMReply(
    True,
    [Claim("Tối đa 5.000.000 đồng mỗi ngày", 1, "Tổng giao dịch mỗi ngày: 5.000.000 đồng.")],
    {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150},
    812,
)
FAKE_KEY = "gsk_FAKE_KEY_FOR_TESTS_0123456789"


class CountingLLM:
    name = "counting"
    prompt_version = "t1"

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, question, passages):
        self.calls += 1
        return REPLY


class ExplodingLLM(CountingLLM):
    def complete(self, question, passages):
        raise AssertionError("the inner model must not be called")


def api_payload(content: dict | None = None, usage: dict | None = None) -> dict:
    content = content or {"answerable": True, "claims": [
        {"text": "Tối đa 5.000.000 đồng mỗi ngày", "source": 1,
         "quote": "Tổng giao dịch mỗi ngày: 5.000.000 đồng."}]}
    return {"choices": [{"message": {"content": json.dumps(content)}}], "usage": usage}


def response(status: int, payload: dict | None = None, headers: dict | None = None) -> httpx.Response:
    request = httpx.Request("POST", "https://example.test/chat/completions")
    return httpx.Response(status, json=payload or {}, headers=headers, request=request)


def test_cache_key_is_stable_and_depends_on_every_input():
    base = cache_key("m", "v1", "q", ["p"])
    assert base == cache_key("m", "v1", "q", ["p"])
    assert len({base, cache_key("m2", "v1", "q", ["p"]), cache_key("m", "v2", "q", ["p"]),
                cache_key("m", "v1", "q2", ["p"]), cache_key("m", "v1", "q", ["p", "p2"])}) == 5


def test_record_calls_the_model_once_then_serves_from_disk(tmp_path):
    inner = CountingLLM()
    cached = CachedLLM(inner, tmp_path, "record")
    first = cached.complete("Hạn mức cấp 1?", PASSAGES)
    second = cached.complete("Hạn mức cấp 1?", PASSAGES)
    assert inner.calls == 1 and (cached.live_calls, cached.hits) == (1, 1)
    assert first == second == REPLY  # claims, tokens and latency all survive the round trip
    assert len(list(tmp_path.glob("*.json"))) == 1 and not list(tmp_path.glob("*.tmp"))


def test_replay_reads_recorded_replies_without_calling_the_model(tmp_path):
    CachedLLM(CountingLLM(), tmp_path, "record").complete("Hạn mức cấp 1?", PASSAGES)
    replay = CachedLLM(ExplodingLLM(), tmp_path, "replay")
    assert replay.complete("Hạn mức cấp 1?", PASSAGES) == REPLY
    assert replay.hits == 1 and replay.misses == 0


def test_replay_miss_raises_and_is_counted_without_calling_the_model(tmp_path):
    replay = CachedLLM(ExplodingLLM(), tmp_path, "replay")
    with pytest.raises(CacheMiss):
        replay.complete("chưa ghi", PASSAGES)
    assert replay.misses == 1 and replay.live_calls == 0


def test_replay_never_touches_the_network(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("replay mode opened a connection")

    monkeypatch.setattr(llm_module.httpx, "post", no_network)
    replay = CachedLLM(OpenAICompatLLM(api_key=None), tmp_path, "replay")
    with pytest.raises(CacheMiss):
        replay.complete("chưa ghi", PASSAGES)


def test_a_damaged_cache_file_counts_as_a_miss(tmp_path):
    record = CachedLLM(CountingLLM(), tmp_path, "record")
    record.complete("q", PASSAGES)
    next(tmp_path.glob("*.json")).write_text("{ not json", encoding="utf-8")
    with pytest.raises(CacheMiss):
        CachedLLM(ExplodingLLM(), tmp_path, "replay").complete("q", PASSAGES)


def test_another_prompt_version_does_not_reuse_old_replies(tmp_path):
    CachedLLM(CountingLLM(), tmp_path, "record").complete("q", PASSAGES)
    newer = CountingLLM()
    newer.prompt_version = "t2"
    with pytest.raises(CacheMiss):
        CachedLLM(newer, tmp_path, "replay").complete("q", PASSAGES)


def test_cache_files_never_contain_the_api_key(tmp_path, monkeypatch):
    seen_headers = {}

    def fake_post(url, headers, json, timeout):
        seen_headers.update(headers)
        return response(200, api_payload(usage={"prompt_tokens": 7, "total_tokens": 9}))

    monkeypatch.setattr(llm_module.httpx, "post", fake_post)
    cached = CachedLLM(OpenAICompatLLM(api_key=FAKE_KEY), tmp_path, "record")
    reply = cached.complete("Hạn mức cấp 1?", PASSAGES)
    assert FAKE_KEY in seen_headers["Authorization"]  # the key really was sent to the API
    text = "".join(p.read_text(encoding="utf-8") for p in tmp_path.iterdir())
    assert FAKE_KEY not in text and "Authorization" not in text and "Bearer" not in text
    assert reply.usage == {"prompt_tokens": 7, "total_tokens": 9}  # missing fields are left out


def test_usage_is_empty_when_the_api_reports_none(monkeypatch):
    monkeypatch.setattr(llm_module.httpx, "post", lambda *a, **k: response(200, api_payload()))
    assert OpenAICompatLLM(api_key=FAKE_KEY).complete("q", PASSAGES).usage == {}


def test_429_waits_for_retry_after_then_succeeds(monkeypatch):
    replies = iter([response(429, headers={"retry-after": "2"}),
                    response(429, headers={"retry-after": "0.5"}),
                    response(200, api_payload())])
    sleeps = []
    monkeypatch.setattr(llm_module.httpx, "post", lambda *a, **k: next(replies))
    monkeypatch.setattr(llm_module.time, "sleep", sleeps.append)
    reply = OpenAICompatLLM(api_key=FAKE_KEY).complete("q", PASSAGES)
    assert reply.answerable and sleeps == [2.0, 0.5]


def test_429_without_retry_after_backs_off_and_is_capped(monkeypatch):
    replies = iter([response(429), response(429, headers={"retry-after": "9999"}),
                    response(200, api_payload())])
    sleeps = []
    monkeypatch.setattr(llm_module.httpx, "post", lambda *a, **k: next(replies))
    monkeypatch.setattr(llm_module.time, "sleep", sleeps.append)
    OpenAICompatLLM(api_key=FAKE_KEY).complete("q", PASSAGES)
    assert sleeps == [1.0, 60.0]


def test_429_gives_up_after_five_retries(monkeypatch):
    calls, sleeps = [], []

    def always_limited(*args, **kwargs):
        calls.append(1)
        return response(429, headers={"retry-after": "1"})

    monkeypatch.setattr(llm_module.httpx, "post", always_limited)
    monkeypatch.setattr(llm_module.time, "sleep", sleeps.append)
    with pytest.raises(httpx.HTTPStatusError):
        OpenAICompatLLM(api_key=FAKE_KEY).complete("q", PASSAGES)
    assert len(calls) == 6 and len(sleeps) == 5


def test_other_errors_are_not_retried(monkeypatch):
    calls = []

    def unauthorized(*args, **kwargs):
        calls.append(1)
        return response(401)

    monkeypatch.setattr(llm_module.httpx, "post", unauthorized)
    monkeypatch.setattr(llm_module.time, "sleep", lambda s: pytest.fail("must not wait"))
    with pytest.raises(httpx.HTTPStatusError):
        OpenAICompatLLM(api_key=FAKE_KEY).complete("q", PASSAGES)
    assert len(calls) == 1


def test_plain_text_refusal_instead_of_json_means_no_answer(monkeypatch):
    body = {"error": {"code": "json_validate_failed", "failed_generation": "I'm sorry, but I can't help with that."}}
    monkeypatch.setattr(llm_module.httpx, "post", lambda *a, **k: response(400, body))
    reply = OpenAICompatLLM(api_key=FAKE_KEY).complete("q", PASSAGES)
    assert not reply.answerable and reply.claims == []


def test_other_400_errors_are_still_raised(monkeypatch):
    monkeypatch.setattr(llm_module.httpx, "post", lambda *a, **k: response(400, {"error": {"code": "model_not_found"}}))
    with pytest.raises(httpx.HTTPStatusError):
        OpenAICompatLLM(api_key=FAKE_KEY).complete("q", PASSAGES)
