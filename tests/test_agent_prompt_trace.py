from __future__ import annotations

from app import agent as agent_module


class ManagedPrompt:
    version = 3

    def compile(self, **variables: str) -> str:
        return (
            f"Feature={variables['feature']}\n"
            f"Docs={variables['docs']}\n"
            f"Question={variables['message']}"
        )


class MockSpan:
    def __init__(self):
        self.metadata = {}
        self.usage = {}
        self.cost = {}

    def update(self, **kwargs):
        self.metadata.update(kwargs.get("metadata", {}))
        if "usage" in kwargs:
            self.usage = kwargs["usage"]
        if "cost" in kwargs:
            self.cost = kwargs["cost"]

    def end(self):
        pass


class RecordingLangfuseClient:
    def __init__(self) -> None:
        self.prompt = ManagedPrompt()
        self.trace_updates: list[dict] = []
        self.generation_updates: list[dict] = []
        self.spans: list[MockSpan] = []

    def get_prompt(self, name: str, **kwargs):
        return self.prompt

    def start_observation(self, **kwargs):
        span = MockSpan()
        span.metadata = kwargs.get("metadata", {})
        self.spans.append(span)
        return span

    def update_current_generation(self, **kwargs) -> None:
        self.generation_updates.append(kwargs)

    def update_current_trace(self, **kwargs) -> None:
        self.trace_updates.append(kwargs)


def test_agent_links_prompt_version_to_trace_and_generation(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    monkeypatch.setenv("LANGFUSE_PROMPT_LABEL", "production")
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)

    agent = agent_module.LabAgent()
    agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Explain traces",
    )

    span = client.spans[-1]
    # Check that prompt metadata fields exist (partial match, not exact)
    assert span.metadata.get("prompt_name") == "day13-chat"
    assert span.metadata.get("prompt_label") == "production"
    assert span.metadata.get("prompt_version") == "3"
    assert span.metadata.get("prompt_source") == "langfuse"
    # Usage should be captured from real API call (tokens > 0)
    assert span.usage.get("input_tokens", 0) > 0
    assert span.usage.get("output_tokens", 0) > 0
