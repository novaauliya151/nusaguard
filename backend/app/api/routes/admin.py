import os
import secrets

from fastapi import APIRouter, Header, HTTPException

from app.api.routes.auth import public_user
from app.models.schemas import AdminDashboardResponse, AdminReport, AdminReportUpdate, UserCreateRequest, UserPublic, UserUpdateRequest
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


@router.get("/users", response_model=list[UserPublic])
def users(x_api_key: str | None = Header(default=None)) -> list[UserPublic]:
    require_admin(x_api_key)
    return [public_user(item) for item in store.list_users()]


@router.post("/users", response_model=UserPublic, status_code=201)
def create_user(payload: UserCreateRequest, x_api_key: str | None = Header(default=None)) -> UserPublic:
    require_admin(x_api_key)
    user = store.create_user(payload.name, payload.email, payload.password, payload.role)
    if not user:
        raise HTTPException(status_code=409, detail="Email sudah terdaftar.")
    return public_user(user)


@router.patch("/users/{user_id}", response_model=UserPublic)
def update_user(user_id: str, payload: UserUpdateRequest, x_api_key: str | None = Header(default=None)) -> UserPublic:
    require_admin(x_api_key)
    user = store.update_user(user_id, payload.role, payload.is_active)
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
    return public_user(user)

