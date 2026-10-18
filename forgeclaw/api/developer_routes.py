from fastapi import APIRouter, BackgroundTasks, HTTPException

from forgeclaw.models.developer import DeveloperRun, DeveloperRunRequest
from forgeclaw.services.developer_mode import DeveloperModeService

router = APIRouter(prefix="/api/v1/developer", tags=["developer-mode"])
service = DeveloperModeService()


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
def start_developer_run(request: DeveloperRunRequest) -> DeveloperRun:
    try:
        return service.start(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs", response_model=list[DeveloperRun])
def list_developer_runs() -> list[DeveloperRun]:
    return service.list_runs()


@router.get("/runs/{run_id}", response_model=DeveloperRun)
def get_developer_run(run_id: str) -> DeveloperRun:
    run = service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Developer run not found.")
    return run
