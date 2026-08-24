from fastapi import APIRouter, HTTPException
from app.models.schemas import ReportRequest, ReportResponse
from app.services.store import store

router = APIRouter(tags=["reports"])

@router.post("/report", response_model=ReportResponse, status_code=201)
def create_report(payload: ReportRequest) -> ReportResponse:
    if not payload.consent:
        raise HTTPException(400, "Persetujuan diperlukan untuk menyimpan laporan secara sukarela.")
    report_id, created_at = store.report(payload.text, payload.category_suggested.value)
    return ReportResponse(id=report_id, created_at=created_at)
