from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


AgentRole = Literal["architect", "critic", "researcher", "judge"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DebateRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=4000)
    context: str = Field(default="", max_length=12000)
    max_rounds: int = Field(default=2, ge=1, le=3)


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: AgentRole
    stage: Literal["proposal", "critique", "revision", "decision"]
    content: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class DebateRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    topic: str
    context: str = ""
    status: Literal["completed", "failed"] = "completed"
    messages: list[AgentMessage] = Field(default_factory=list)
    decision: str
    unresolved_questions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class DebateSummary(BaseModel):
    id: str
    topic: str
    status: str
    decision: str
    created_at: datetime
