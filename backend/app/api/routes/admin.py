from fastapi import APIRouter, Header, HTTPException

from app.api.routes.auth import bearer_admin, public_user
from app.api.routes.content import anonymize_report
from app.models.schemas import AdminDashboardResponse, AdminReport, AdminReportUpdate, DatasetCandidate, DatasetCandidateRequest, EducationItem, EducationItemRequest, PasswordChangeRequest, PublicDatasetRow, ReportValidationRequest, UserCreateRequest, UserPublic, UserUpdateRequest
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
        analyses_today=snapshot["today_total"], analyses_this_month=snapshot["month_total"],
        reports_reviewed=snapshot["reports_reviewed"], candidates_total=snapshot["candidates_total"],
        education_published=snapshot["education_published"],
    )


@router.get("/reports/{report_id}")
def report_detail(report_id: str, authorization: str | None = Header(default=None)) -> dict:
    require_admin(authorization)
    report = store.get_report(report_id)
    if not report: raise HTTPException(404, "Laporan tidak ditemukan.")
    return report


@router.patch("/reports/{report_id}/validate")
def validate_report(report_id: str, payload: ReportValidationRequest, authorization: str | None = Header(default=None)) -> dict:
    admin = require_admin(authorization)
    report = store.validate_report(report_id, payload.model_dump())
    if not report: raise HTTPException(404, "Laporan tidak ditemukan.")
    store.add_activity(admin["email"], "validate_report", "report", report_id, payload.status)
    return report


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
    try:
        user = store.update_user(user_id, payload.role, payload.is_active, payload.name, payload.email, payload.password)
    except Exception as exc:
        if "unique" in str(exc).casefold() or "duplicate" in str(exc).casefold():
            raise HTTPException(status_code=409, detail="Email sudah digunakan.") from exc
        raise
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
    return public_user(user)


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str, authorization: str | None = Header(default=None)) -> None:
    admin = require_admin(authorization)
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="Admin tidak dapat menghapus akun yang sedang digunakan.")
    if not store.delete_user(user_id):
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")


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
    admin = require_admin(authorization)
    report = store.get_report(report_id)
    if not report or report["status"] not in {"reviewed", "approved"}: raise HTTPException(400, "Laporan harus disetujui sebelum masuk dataset.")
    row = store.publish_report_dataset(report_id, anonymize_report(report["text"]))
    candidate = store.save_candidate(None, {"report_id":report_id,"text_anonymized":anonymize_report(report["text"]),"category":report.get("correct_category") or report["category_suggested"],"source":"community_report","data_type":"primer","validation_status":"pending","split":None,"validator":admin["email"],"notes":report.get("validation_notes"),"is_duplicate":False,"is_archived":False,"nseae_validation":{}})
    store.validate_report(report_id, {"status":"dataset_candidate"})
    store.add_activity(admin["email"], "create_candidate", "dataset_candidate", candidate["id"], report_id)
    return PublicDatasetRow(**row)


@router.get("/candidates", response_model=list[DatasetCandidate])
def candidates(authorization: str | None = Header(default=None)) -> list[DatasetCandidate]:
    require_admin(authorization)
    return [DatasetCandidate(**item) for item in store.candidates()]


@router.post("/candidates", response_model=DatasetCandidate, status_code=201)
def create_candidate(payload: DatasetCandidateRequest, authorization: str | None = Header(default=None)) -> DatasetCandidate:
    admin=require_admin(authorization);item=store.save_candidate(None,{**payload.model_dump(),"validator":payload.validator or admin["email"]});store.add_activity(admin["email"],"create_candidate","dataset_candidate",item["id"]);return DatasetCandidate(**item)


@router.patch("/candidates/{candidate_id}", response_model=DatasetCandidate)
def update_candidate(candidate_id: str, payload: DatasetCandidateRequest, authorization: str | None = Header(default=None)) -> DatasetCandidate:
    admin=require_admin(authorization);item=store.save_candidate(candidate_id,{**payload.model_dump(),"validator":payload.validator or admin["email"]});store.add_activity(admin["email"],"update_candidate","dataset_candidate",candidate_id);return DatasetCandidate(**item)


@router.delete("/candidates/{candidate_id}", status_code=204)
def archive_candidate(candidate_id: str, authorization: str | None = Header(default=None)) -> None:
    admin=require_admin(authorization)
    if not store.archive_candidate(candidate_id):raise HTTPException(404,"Kandidat tidak ditemukan.")
    store.add_activity(admin["email"],"archive_candidate","dataset_candidate",candidate_id)


@router.get("/activities")
def activities(authorization: str | None = Header(default=None)) -> list[dict]:
    require_admin(authorization);return store.activities()


@router.post("/profile/password", status_code=204)
def change_password(payload: PasswordChangeRequest, authorization: str | None = Header(default=None)) -> None:
    admin=require_admin(authorization)
    if not store.change_password(admin["id"],payload.current_password,payload.new_password):raise HTTPException(400,"Password lama tidak sesuai.")
    store.add_activity(admin["email"],"change_password","admin_profile",admin["id"])

