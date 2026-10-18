from fastapi import APIRouter, HTTPException, Query

from forgeclaw.core.settings import settings
from forgeclaw.models.debate import DebateRecord, DebateRequest, DebateSummary
from forgeclaw.services.debate_service import DebateService
from forgeclaw.storage.database import get_debate, list_debates, save_debate

router = APIRouter(prefix="/api/v1", tags=["debates"])
service = DebateService()


@router.post("/debates", response_model=DebateRecord, status_code=201)
def create_debate(request: DebateRequest) -> DebateRecord:
    record = service.run(request)
    save_debate(settings.database_path, record.model_dump(mode="json"))
    return record


@router.get("/debates", response_model=list[DebateSummary])
def get_debates(limit: int = Query(default=20, ge=1, le=100)) -> list[dict]:
    return list_debates(settings.database_path, limit)


@router.get("/debates/{debate_id}", response_model=DebateRecord)
def read_debate(debate_id: str) -> dict:
    record = get_debate(settings.database_path, debate_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Debate not found")
    return record
