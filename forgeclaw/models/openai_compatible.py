from __future__ import annotations

import httpx

from forgeclaw.core.settings import settings


class ModelProviderError(RuntimeError):
    """Raised when a configured model provider cannot complete a request."""


class OpenAICompatibleClient:
    """Minimal client for providers exposing POST /chat/completions."""

    def __init__(self) -> None:
        self.base_url = settings.llm_base_url.rstrip("/")
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model
        self.timeout = settings.llm_timeout_seconds

    @property
    def is_configured(self) -> bool:
        # API keys are optional for local endpoints such as Ollama-compatible gateways.
        return bool(self.base_url and self.model)

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        if not self.is_configured:
            raise ModelProviderError("LLM_BASE_URL and LLM_MODEL must be configured.")

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
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
            # Do not include headers, tokens, or full provider payloads in the exception.
            raise ModelProviderError(
                f"Model request failed ({type(exc).__name__}). Check endpoint, credentials, and provider logs."
            ) from exc
