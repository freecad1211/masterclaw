from __future__ import annotations

import os

from forgeclaw.models.openai_compatible import OpenAICompatibleClient


class AgentModelRouter:
    """Resolve per-role model settings, falling back to the global provider."""

    def client_for(self, role: str) -> OpenAICompatibleClient:
        prefix = f"FORGECLAW_AGENT_{role.upper()}_"
        overrides = {
            "base_url": os.getenv(prefix + "BASE_URL", "").strip(),
            "api_key": os.getenv(prefix + "API_KEY", ""),
            "model": os.getenv(prefix + "MODEL", "").strip(),
            "timeout_seconds": os.getenv(prefix + "TIMEOUT_SECONDS", ""),
        }
        return OpenAICompatibleClient(overrides=overrides)

    def available_profiles(self) -> list[dict[str, str | bool]]:
        profiles = []
        for role in ("architect", "implementer", "reviewer", "tester", "integrator"):
            client = self.client_for(role)
            profiles.append({
                "role": role,
                "model": client.model or "(not configured)",
                "base_url": client.base_url or "(not configured)",
                "configured": client.is_configured,
            })
        return profiles
