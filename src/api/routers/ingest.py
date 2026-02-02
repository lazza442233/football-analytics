from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


class IngestRequest(BaseModel):
    competition_id: int
    season_id: int
    ingest_events: bool = True


@router.post("/", status_code=202)
async def trigger_ingestion(request: Request, payload: IngestRequest):
    """
    Trigger a background ingestion job for a specific competition and season.
    """
    if not hasattr(request.app.state, "arq_pool"):
        raise HTTPException(status_code=503, detail="Background worker unavailable")

    job_id = f"ingest_season_{payload.competition_id}_{payload.season_id}"
    job = await request.app.state.arq_pool.enqueue_job(
        "ingest_season_task",
        _job_id=job_id,
        competition_id=payload.competition_id,
        season_id=payload.season_id,
        ingest_events=payload.ingest_events,
    )
    return {"job_id": job.job_id, "status": "queued", "payload": payload}
