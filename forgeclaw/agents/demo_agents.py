from forgeclaw.models.debate import AgentMessage, DebateRequest


class DemoArchitect:
    role = "architect"

    def propose(self, request: DebateRequest) -> AgentMessage:
        return AgentMessage(
            role="architect",
            stage="proposal",
            content=(
                f"Topic: {request.topic}. Start with a small, testable design; "
                "separate orchestration, model adapters, and storage. Record assumptions "
                "and defer irreversible actions."
            ),
            evidence=["Deterministic demo fixture; not model-generated evidence."],
        )


class DemoCritic:
    role = "critic"

    def critique(self, request: DebateRequest, proposal: AgentMessage) -> AgentMessage:
        return AgentMessage(
            role="critic",
            stage="critique",
            content=(
                "Check failure recovery, permissions, timeouts, and whether the proposal "
                "can be tested without a live model. A plausible proposal is not verified fact."
            ),
            evidence=["Deterministic demo fixture; illustrative critique only."],
        )


class DemoJudge:
    role = "judge"

    def decide(
        self, request: DebateRequest, proposal: AgentMessage, critique: AgentMessage
    ) -> AgentMessage:
        return AgentMessage(
            role="judge",
            stage="decision",
            content=(
                "Decision: implement the smallest testable slice first, keep side effects "
                "behind explicit adapters, and add real model/Obsidian integrations after "
                "local API and persistence tests pass. The exact FreeLLM endpoint and API "
                "compatibility still need confirmation."
            ),
            evidence=["Synthesized from deterministic demo proposal and critique; no live model or external sources used."],
        )
