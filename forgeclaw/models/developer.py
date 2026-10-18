from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


AgentKind = Literal["architect", "implementer", "reviewer", "tester", "integrator"]
RunStatus = Literal["queued", "planning", "running", "reviewing", "integrating", "completed", "failed", "needs_approval"]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class AgentProfile(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    role: AgentKind
    model: str | None = None
    base_url: str | None = None
    temperature: float = Field(default=0.1, ge=0, le=1)
    max_tokens: int = Field(default=8000, ge=256, le=32000)


class DeveloperTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=5, max_length=8000)
    owner: AgentKind = "implementer"
    depends_on: list[str] = Field(default_factory=list)
    allowed_paths: list[str] = Field(default_factory=list)
    branch: str = ""
    status: Literal["queued", "running", "reviewing", "passed", "failed", "blocked"] = "queued"
    commit_sha: str | None = None
    test_output: str = ""
    review_output: str = ""


class DeveloperRunRequest(BaseModel):
    goal: str = Field(min_length=8, max_length=12000)
    repo_path: str = Field(min_length=1, max_length=1000)
    base_branch: str = "main"
    max_agents: int = Field(default=3, ge=1, le=6)
    max_revisions: int = Field(default=2, ge=0, le=3)
    auto_merge: bool = False
    tasks: list[DeveloperTask] = Field(default_factory=list, max_length=12)


class AgentEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    agent: str
    event_type: Literal["message", "status", "tool", "review", "test", "commit", "merge", "error"]
    content: str = Field(max_length=20000)
    task_id: str | None = None
    created_at: datetime = Field(default_factory=now_utc)


class DeveloperRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    goal: str
    repo_path: str
    base_branch: str
    status: RunStatus = "queued"
    tasks: list[DeveloperTask] = Field(default_factory=list)
    events: list[AgentEvent] = Field(default_factory=list)
    integration_branch: str = ""
    final_commit: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)
