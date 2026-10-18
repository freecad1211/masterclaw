from typing import Protocol

from forgeclaw.models.debate import AgentMessage, DebateRequest


class DebateAgent(Protocol):
    role: str

    def propose(self, request: DebateRequest) -> AgentMessage: ...
    def critique(self, request: DebateRequest, proposal: AgentMessage) -> AgentMessage: ...
