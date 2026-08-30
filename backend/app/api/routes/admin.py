from fastapi import APIRouter, Header, HTTPException

from app.api.routes.auth import bearer_admin, public_user
from app.api.routes.content import anonymize_report
from app.models.schemas import AdminDashboardResponse, AdminReport, AdminReportUpdate, EducationItem, EducationItemRequest, PublicDatasetRow, UserCreateRequest, UserPublic, UserUpdateRequest
from app.services.predictor import _pipeline
from app.services.store import store

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(authorization: str | None = Header(default=None)) -> dict:
    return bearer_admin(authorization)


@router.get("/dashboard", response_model=AdminDashboardResponse, dependencies=[])
def dashboard(authorization: str | None = Header(default=None)) -> AdminDashboardResponse:
    require_admin(authorization)
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
def moderate_report(report_id: str, payload: AdminReportUpdate, authorization: str | None = Header(default=None)) -> AdminReportUpdate:
    require_admin(authorization)
    if not store.update_report_status(report_id, payload.status):
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan.")
    return payload


@router.get("/users", response_model=list[UserPublic])
def users(authorization: str | None = Header(default=None)) -> list[UserPublic]:
    require_admin(authorization)
    return [public_user(item) for item in store.list_users()]


@router.post("/users", response_model=UserPublic, status_code=201)
def create_user(payload: UserCreateRequest, authorization: str | None = Header(default=None)) -> UserPublic:
    require_admin(authorization)
    user = store.create_user(payload.name, payload.email, payload.password, payload.role)
    if not user:
        raise HTTPException(status_code=409, detail="Email sudah terdaftar.")
    return public_user(user)


@router.patch("/users/{user_id}", response_model=UserPublic)
def update_user(user_id: str, payload: UserUpdateRequest, authorization: str | None = Header(default=None)) -> UserPublic:
    require_admin(authorization)
    user = store.update_user(user_id, payload.role, payload.is_active)
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
    return public_user(user)


@router.get("/education", response_model=list[EducationItem])
def education_items(authorization: str | None = Header(default=None)) -> list[EducationItem]:
    require_admin(authorization)
    return [EducationItem(**item) for item in store.education(False)]


@router.post("/education", response_model=EducationItem, status_code=201)
def create_education(payload: EducationItemRequest, authorization: str | None = Header(default=None)) -> EducationItem:
    require_admin(authorization)
    return EducationItem(**store.save_education(None, payload.model_dump(mode="json")))


@router.patch("/education/{item_id}", response_model=EducationItem)
def update_education(item_id: str, payload: EducationItemRequest, authorization: str | None = Header(default=None)) -> EducationItem:
    require_admin(authorization)
    return EducationItem(**store.save_education(item_id, payload.model_dump(mode="json")))


@router.delete("/education/{item_id}", status_code=204)
def delete_education(item_id: str, authorization: str | None = Header(default=None)) -> None:
    require_admin(authorization)
    if not store.delete_education(item_id): raise HTTPException(404, "Konten tidak ditemukan.")


@router.post("/reports/{report_id}/dataset", response_model=PublicDatasetRow, status_code=201)
def process_report(report_id: str, authorization: str | None = Header(default=None)) -> PublicDatasetRow:
    require_admin(authorization)
    report = store.get_report(report_id)
    if not report or report["status"] != "reviewed": raise HTTPException(400, "Laporan harus ditinjau sebelum masuk dataset.")
    row = store.publish_report_dataset(report_id, anonymize_report(report["text"]))
    return PublicDatasetRow(**row)

