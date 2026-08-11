from __future__ import annotations

from app import cost_config as cc
from app.incidents import STATE


def _reset_config() -> None:
    cc.update_config(
        {
            "max_output_tokens": 0,
            "cache_enabled": False,
            "cache_ttl_seconds": 60,
        }
    )
    cc.cache_clear()


def test_update_config_tracks_before_after(monkeypatch) -> None:
    monkeypatch.setattr(cc, "CONFIG", {"max_output_tokens": 0, "cache_enabled": False, "cache_ttl_seconds": 60})
    config, changed = cc.update_config({"max_output_tokens": 150})
    assert changed == {"max_output_tokens": (0, 150)}
    assert config["max_output_tokens"] == 150
    assert cc.get_config()["max_output_tokens"] == 150


def test_update_config_rejects_unknown_and_invalid() -> None:
    _reset_config()
    try:
        cc.update_config({"unknown_key": 1})
        raise AssertionError("phải raise KeyError")
    except KeyError:
        pass
    try:
        cc.update_config({"max_output_tokens": -1})
        raise AssertionError("phải raise ValueError")
    except ValueError:
        pass


def test_cache_ttl(monkeypatch) -> None:
    _reset_config()
    monkeypatch.setattr(cc, "CONFIG", {"max_output_tokens": 0, "cache_enabled": True, "cache_ttl_seconds": 60})
    now = [1000.0]
    monkeypatch.setattr(cc.time, "monotonic", lambda: now[0])

    cc.cache_put("qa", "hello", "answer")
    assert cc.cache_get("qa", "hello") == "answer"
    assert cc.cache_get("qa", "other") is None

    now[0] = 1050.0
    assert cc.cache_get("qa", "hello") == "answer"

    now[0] = 1061.0
    assert cc.cache_get("qa", "hello") is None


def test_max_output_tokens_caps_mock_generation(monkeypatch) -> None:
    from app import mock_llm
    from app.mock_llm import FakeLLM

    monkeypatch.setattr(mock_llm, "get_openai_client", lambda: None)
    _reset_config()
    STATE["cost_spike"] = True
    try:
        uncapped = FakeLLM().generate("t")
        assert uncapped.usage.output_tokens > 150

        cc.update_config({"max_output_tokens": 150})
        capped = FakeLLM().generate("t")
        assert capped.usage.output_tokens <= 150
    finally:
        STATE["cost_spike"] = False
        _reset_config()


class _Prompt:
    version = "1"
    is_fallback = False

    def compile(self, **variables) -> str:
        return "compiled prompt"


class _RecordingClient:
    def get_prompt(self, *args, **kwargs):
        return _Prompt()

    def update_current_trace(self, **kwargs) -> None:
        pass

    def update_current_generation(self, **kwargs) -> None:
        pass


def test_agent_cache_hit_zero_cost(monkeypatch) -> None:
    from app import agent as agent_module
    from app import mock_llm

    monkeypatch.setattr(mock_llm, "get_openai_client", lambda: None)
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: _RecordingClient())
    _reset_config()
    cc.update_config({"cache_enabled": True, "cache_ttl_seconds": 60})

    agent = agent_module.LabAgent()
    first = agent_module.LabAgent.run.__wrapped__(
        agent, user_id="u1", feature="qa", session_id="s1", message="duplicate question"
    )
    second = agent_module.LabAgent.run.__wrapped__(
        agent, user_id="u1", feature="qa", session_id="s2", message="duplicate question"
    )

    assert first.cost_usd > 0
    assert second.cost_usd == 0
    assert second.tokens_out == 0
    cc.cache_clear()

