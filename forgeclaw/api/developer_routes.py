import hmac
import os

from fastapi import APIRouter, Depends, Header, HTTPException

from forgeclaw.models.developer import AgentMessageRequest, DeveloperRun, DeveloperRunRequest
from forgeclaw.services.developer_mode import DeveloperModeService

router = APIRouter(prefix="/api/v1/developer", tags=["developer-mode"])
service = DeveloperModeService()


def require_developer_token(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("FORGECLAW_API_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Developer Mode is locked. Configure FORGECLAW_API_TOKEN first.")
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="A valid Bearer token is required for Developer Mode actions.")


@router.get("/profiles")
def list_agent_profiles() -> list[dict[str, str | bool]]:
    return service.profiles()


@router.get("/skills")
def list_builtin_skills() -> list[dict[str, object]]:
    return service.skills()


@router.get("/mcp-tools")
def list_builtin_mcp_tools() -> list[dict[str, str]]:
    return service.tools()


@router.post("/runs", response_model=DeveloperRun, status_code=202)
def start_developer_run(
    request: DeveloperRunRequest,
    _: None = Depends(require_developer_token),
) -> DeveloperRun:
    try:
        return service.start(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs", response_model=list[DeveloperRun])
def list_developer_runs(_: None = Depends(require_developer_token)) -> list[DeveloperRun]:
    return service.list_runs()


@router.get("/runs/{run_id}", response_model=DeveloperRun)
def get_developer_run(run_id: str, _: None = Depends(require_developer_token)) -> DeveloperRun:
    run = service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Developer run not found.")
    return run


@router.post("/runs/{run_id}/messages")
def send_agent_message(
    run_id: str,
    request: AgentMessageRequest,
    _: None = Depends(require_developer_token),
) -> dict[str, object]:
    try:
        event = service.send_message(run_id, request.sender, request.recipient, request.content, request.task_id)
        return event.model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runs/{run_id}/approve-merge", response_model=DeveloperRun)
def approve_local_merge(run_id: str, _: None = Depends(require_developer_token)) -> DeveloperRun:
    try:
        return service.approve_merge(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
