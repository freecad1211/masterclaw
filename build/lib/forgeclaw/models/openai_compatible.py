from __future__ import annotations

from typing import Any

import httpx

from forgeclaw.core.settings import settings


class ModelProviderError(RuntimeError):
    """Raised when a configured model provider cannot complete a request."""


class OpenAICompatibleClient:
    """Minimal client for providers exposing POST /chat/completions."""

    def __init__(self, overrides: dict[str, Any] | None = None) -> None:
        overrides = overrides or {}
        self.base_url = str(overrides.get("base_url") or settings.llm_base_url).rstrip("/")
        self.api_key = str(overrides.get("api_key") or settings.llm_api_key)
        self.model = str(overrides.get("model") or settings.llm_model).strip()
        self.timeout = float(overrides.get("timeout_seconds") or settings.llm_timeout_seconds)
        self.temperature = float(overrides.get("temperature", 0.1))

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.model)

    def complete(self, *, system_prompt: str, user_prompt: str, temperature: float | None = None) -> str:
        if not self.is_configured:
            raise ModelProviderError("Configure LLM_BASE_URL and LLM_MODEL or the corresponding role-specific settings.")

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature if temperature is None else temperature,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ModelProviderError("The model provider returned empty content.")
            return content.strip()
        except ModelProviderError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise ModelProviderError(
                f"Model request failed ({type(exc).__name__}). Check endpoint, credentials, and provider logs."
            ) from exc
