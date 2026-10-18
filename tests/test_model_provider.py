import httpx
import pytest

from forgeclaw.core.settings import settings
from forgeclaw.models.openai_compatible import ModelProviderError, OpenAICompatibleClient


def test_openai_compatible_client_sends_chat_completion(monkeypatch):
    monkeypatch.setattr(settings, "llm_base_url", "https://models.example/v1")
    monkeypatch.setattr(settings, "llm_api_key", "test-secret")
    monkeypatch.setattr(settings, "llm_model", "demo-model")
    captured = {}

    def fake_post(url, *, headers, json, timeout):
        captured.update(url=url, headers=headers, json=json, timeout=timeout)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Decision draft"}}]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("forgeclaw.models.openai_compatible.httpx.post", fake_post)
    client = OpenAICompatibleClient()

    assert client.complete(system_prompt="Be precise", user_prompt="Review this") == "Decision draft"
    assert captured["url"] == "https://models.example/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-secret"
    assert captured["json"]["model"] == "demo-model"
    assert captured["json"]["messages"][0] == {"role": "system", "content": "Be precise"}


def test_unconfigured_client_fails_clearly(monkeypatch):
    monkeypatch.setattr(settings, "llm_base_url", "")
    monkeypatch.setattr(settings, "llm_model", "")
    client = OpenAICompatibleClient()

    with pytest.raises(ModelProviderError, match="LLM_BASE_URL and LLM_MODEL"):
        client.complete(system_prompt="system", user_prompt="user")
