"""
Demo agents for demonstrating the debate workflow.

These agents are deterministic, for testing and development of the debate harness
and UI, rather than for actual debate sessions with LLMs.
"""

from __future__ import annotations

from forgeclaw.agents.base import BaseDebateAgent
from forgeclaw.models.debate import AgentMessage, DebateRequest


class DemoArchitect(BaseDebateAgent):
    """A deterministic architect agent for demonstration."""

    role = "architect"

    def propose(self, request: DebateRequest) -> AgentMessage:
        self._log(f"Proposing for topic: {request.topic}")
        return AgentMessage(
            role=self.role,
            stage="proposal",
            content=(
                f"Topic: {request.topic}. Start with a small, testable design; "
                "separate orchestration, model adapters, and storage. Record assumptions "
                "and defer irreversible actions."
            ),
            evidence=["Deterministic demo fixture; not model-generated evidence."],
        )

    def critique(self, request: DebateRequest, proposal: AgentMessage) -> AgentMessage:
        raise NotImplementedError("Architect does not critique.")

    def decide(
        self, request: DebateRequest, proposal: AgentMessage, critique: AgentMessage
    ) -> AgentMessage:
        raise NotImplementedError("Architect does not decide.")


class DemoCritic(BaseDebateAgent):
    """A deterministic critic agent for demonstration."""

    role = "critic"

    def propose(self, request: DebateRequest) -> AgentMessage:
        raise NotImplementedError("Critic does not propose.")

    def critique(self, request: DebateRequest, proposal: AgentMessage) -> AgentMessage:
        self._log(f"Critiquing proposal for topic: {request.topic}")
        return AgentMessage(
            role=self.role,
            stage="critique",
            content=(
                "Check failure recovery, permissions, timeouts, and whether the proposal "
                "can be tested without a live model. A plausible proposal is not verified fact."
            ),
            evidence=["Deterministic demo fixture; illustrative critique only."],
        )

    def decide(
        self, request: DebateRequest, proposal: AgentMessage, critique: AgentMessage
    ) -> AgentMessage:
        raise NotImplementedError("Critic does not decide.")


class DemoJudge(BaseDebateAgent):
    """A deterministic judge agent for demonstration."""

    role = "judge"

    def propose(self, request: DebateRequest) -> AgentMessage:
        raise NotImplementedError("Judge does not propose.")

    def critique(self, request: DebateRequest, proposal: AgentMessage) -> AgentMessage:
        raise NotImplementedError("Judge does not critique.")

    def decide(
        self, request: DebateRequest, proposal: AgentMessage, critique: AgentMessage
    ) -> AgentMessage:
        self._log(f"Deciding for topic: {request.topic}")
        return AgentMessage(
            role=self.role,
            stage="decision",
            content=(
                "Decision: implement the smallest testable slice first, keep side effects "
                "behind explicit adapters, and add real model/Obsidian integrations after "
                "local API and persistence tests pass. The exact FreeLLM endpoint and API "
                "compatibility still need confirmation."
            ),
            evidence=["Synthesized from deterministic demo proposal and critique."],
        )


__all__ = ["DemoArchitect", "DemoCritic", "DemoJudge"]
