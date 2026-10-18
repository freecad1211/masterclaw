from forgeclaw.agents import DemoArchitect, DemoCritic, DemoJudge
from forgeclaw.models.debate import DebateRequest

def test_demo_agents_integration():
    request = DebateRequest(topic="Improve agent structure")

    architect = DemoArchitect()
    proposal = architect.propose(request)
    assert proposal.role == "architect"
    assert "testable design" in proposal.content

    critic = DemoCritic()
    critique = critic.critique(request, proposal)
    assert critique.role == "critic"
    assert "failure recovery" in critique.content

    judge = DemoJudge()
    decision = judge.decide(request, proposal, critique)
    assert decision.role == "judge"
    assert "Decision:" in decision.content
