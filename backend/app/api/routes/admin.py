import os
import secrets

from fastapi import APIRouter, Header, HTTPException

from app.models.schemas import AdminDashboardResponse, AdminReport, AdminReportUpdate
from app.services.predictor import _pipeline
from app.services.store import store

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("ADMIN_API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="ADMIN_API_KEY belum dikonfigurasi.")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Kunci admin tidak valid.")


@router.get("/dashboard", response_model=AdminDashboardResponse, dependencies=[])
def dashboard(x_api_key: str | None = Header(default=None)) -> AdminDashboardResponse:
    require_admin(x_api_key)
    snapshot = store.admin_dashboard()
    return AdminDashboardResponse(
        total_analyzed=snapshot["total"],
        category_counts=snapshot["counts"],
        reports_total=snapshot["reports_total"],
        reports_pending=snapshot["reports_pending"],
        recent_reports=[AdminReport(**item) for item in snapshot["reports"]],
        model_status="IndoBERT" if _pipeline() is not None else "Rules fallback",
        privacy_mode="Ephemeral — isi analisis tidak disimpan",
        daily_stats=snapshot["daily"],
        source_counts=snapshot["sources"],
        database_engine=snapshot["database_engine"],
        database_connected=True,
    )


@router.patch("/reports/{report_id}", response_model=AdminReportUpdate)
def moderate_report(report_id: str, payload: AdminReportUpdate, x_api_key: str | None = Header(default=None)) -> AdminReportUpdate:
    require_admin(x_api_key)
    if not store.update_report_status(report_id, payload.status):
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan.")
    return payload

