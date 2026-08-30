from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.dependencies import get_current_user
from models.user import User
from workers.celery_app import celery_app

router = APIRouter(prefix="/jobs", tags=["jobs"])

READY_STATES = {"SUCCESS", "FAILURE"}


class JobStatusOut(BaseModel):
    task_id: str
    state: str
    result: dict | None = None
    error: str | None = None


@router.get("/{task_id}", response_model=JobStatusOut)
def get_job_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> JobStatusOut:
    result = celery_app.AsyncResult(task_id)
    state = result.state
    out = JobStatusOut(task_id=task_id, state=state)
    if state not in READY_STATES:
        return out
    if state == "SUCCESS":
        try:
            payload = result.result
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail=f"Cannot read job result: {exc}") from exc
        if isinstance(payload, dict):
            out.result = payload
        return out
    try:
        exc = result.result
        out.error = str(exc) if exc is not None else "task failed"
    except Exception:  # pragma: no cover - defensive
        out.error = "task failed"
    return out