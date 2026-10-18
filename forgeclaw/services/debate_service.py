from datetime import datetime, timezone

from forgeclaw.agents.demo_agents import DemoArchitect, DemoCritic, DemoJudge
from forgeclaw.core.settings import settings
from forgeclaw.models.debate import DebateRecord, DebateRequest


class DebateService:
    def __init__(self, database_path: str | None = None) -> None:
        self.database_path = database_path or settings.database_path
        self.architect = DemoArchitect()
        self.critic = DemoCritic()
        self.judge = DemoJudge()

    def run(self, request: DebateRequest) -> DebateRecord:
        proposal = self.architect.propose(request)
        critique = self.critic.critique(request, proposal)
        decision = self.judge.decide(request, proposal, critique)
        return DebateRecord(
            topic=request.topic,
            context=request.context,
            messages=[proposal, critique, decision],
            decision=decision.content,
            unresolved_questions=[
                "Confirm the model provider and API compatibility.",
                "Choose secure Obsidian connectivity: private network, authenticated tunnel, or server-side Vault sync.",
            ],
            created_at=datetime.now(timezone.utc),
        )
