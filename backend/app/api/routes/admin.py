import csv
import base64
import io
import json
import re
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.routes.auth import bearer_admin, bearer_permission, public_user
from app.api.routes.content import anonymize_report
from app.models.schemas import AdminDashboardResponse, AdminReport, AdminReportUpdate, AnalyzeRequest, DatasetCandidate, DatasetCandidateRequest, EducationItem, EducationItemRequest, PasswordChangeRequest, PasswordResetRequest, PublicDatasetRow, ReportValidationRequest, RoleRequest, UserCreateRequest, UserPublic, UserUpdateRequest
from app.api.routes.analyze import analyze
from app.services.admin_domain import CATEGORIES, INDICATORS, canonical_role
from app.services.predictor import _pipeline
from app.services.store import admin_domain, store

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(authorization: str | None = Header(default=None)) -> dict:
    return bearer_admin(authorization)

def require(authorization: str | None, permission: str) -> dict:
    return bearer_permission(authorization, permission)


@router.get("/dashboard", response_model=AdminDashboardResponse, dependencies=[])
def dashboard(authorization: str | None = Header(default=None)) -> AdminDashboardResponse:
    require(authorization, "dashboard.view")
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
    require(authorization, "reports.view")
    report = store.get_report(report_id)
    if not report: raise HTTPException(404, "Laporan tidak ditemukan.")
    return report


@router.patch("/reports/{report_id}/validate")
def validate_report(report_id: str, payload: ReportValidationRequest, authorization: str | None = Header(default=None)) -> dict:
    admin = require(authorization, "reports.review")
    if payload.status == "rejected" and not payload.validation_notes: raise HTTPException(422,"Alasan penolakan wajib diisi.")
    data=payload.model_dump();data.update({"reviewer_id":admin["id"],"reviewed_at":datetime.utcnow(),"updated_at":datetime.utcnow()})
    if payload.status=="rejected":data["rejection_reason"]=payload.validation_notes
    report = store.validate_report(report_id, data)
    if not report: raise HTTPException(404, "Laporan tidak ditemukan.")
    store.add_activity(admin["email"], "validate_report", "report", report_id, payload.status)
    return report


@router.patch("/reports/{report_id}", response_model=AdminReportUpdate)
def moderate_report(report_id: str, payload: AdminReportUpdate, authorization: str | None = Header(default=None)) -> AdminReportUpdate:
    require(authorization, "reports.review")
    if not store.update_report_status(report_id, payload.status):
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan.")
    return payload


@router.get("/users")
def users(q: str = "", role: str | None = None, status: str | None = None, authorization: str | None = Header(default=None)) -> list[dict]:
    require(authorization, "users.view")
    return admin_domain.list_users(q, role, status)

@router.get("/users/{user_id}")
def user_detail(user_id: str, authorization: str | None = Header(default=None)) -> dict:
    require(authorization, "users.view"); item = admin_domain.user_detail(user_id)
    if not item: raise HTTPException(404, "Pengguna tidak ditemukan.")
    return item


@router.post("/users", status_code=201)
def create_user(payload: UserCreateRequest, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "users.create")
    if payload.confirm_password is not None and payload.password != payload.confirm_password: raise HTTPException(422, "Konfirmasi password tidak sama.")
    try: user = admin_domain.create_internal_user(payload.model_dump(exclude={"confirm_password"}), actor["id"])
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    if not user:
        raise HTTPException(status_code=409, detail="Email sudah terdaftar.")
    admin_domain.save_activity(actor, "create", "users", user["id"], "Menambahkan pengguna", new_values={"name": user["name"], "email": user["email"], "role": user["role"], "status": user["status"]})
    return user


@router.patch("/users/{user_id}")
def update_user(user_id: str, payload: UserUpdateRequest, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "users.update"); before = admin_domain.user_detail(user_id)
    try:
        data = payload.model_dump(exclude_none=True)
        if payload.is_active is not None and "status" not in data: data["status"] = "active" if payload.is_active else "suspended"
        user = admin_domain.update_internal_user(user_id, data, actor)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    admin_domain.save_activity(actor, "update", "users", user_id, "Memperbarui pengguna", old_values=before, new_values={key: user.get(key) for key in ("name", "email", "role", "status")})
    return user

@router.post("/users/{user_id}/reset-password", status_code=204)
def reset_user_password(user_id: str, payload: PasswordResetRequest, authorization: str | None = Header(default=None)) -> None:
    actor = require(authorization, "users.update")
    if payload.password != payload.confirm_password: raise HTTPException(422, "Konfirmasi password tidak sama.")
    try: admin_domain.reset_password(user_id, payload.password, payload.must_change_password)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    admin_domain.save_activity(actor, "reset_password", "users", user_id, "Password pengguna direset; nilai password tidak dicatat")


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str, authorization: str | None = Header(default=None)) -> None:
    actor = require(authorization, "users.delete")
    try: admin_domain.soft_delete_user(user_id, actor)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    admin_domain.save_activity(actor, "soft_delete", "users", user_id, "Menghapus pengguna secara lunak")


@router.get("/education", response_model=list[EducationItem])
def education_items(authorization: str | None = Header(default=None)) -> list[EducationItem]:
    require(authorization, "education.view")
    return [EducationItem(**item) for item in store.education(False)]


@router.post("/education", response_model=EducationItem, status_code=201)
def create_education(payload: EducationItemRequest, authorization: str | None = Header(default=None)) -> EducationItem:
    actor=require(authorization, "education.create")
    try:item=store.save_education(None,{**payload.model_dump(mode="json"),"is_published":payload.status=="published"})
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    admin_domain.save_activity(actor,"create","education",item["id"],"Menambahkan konten edukasi",new_values={"title":item["title"],"status":item["status"]});return EducationItem(**item)


@router.patch("/education/{item_id}", response_model=EducationItem)
def update_education(item_id: str, payload: EducationItemRequest, authorization: str | None = Header(default=None)) -> EducationItem:
    actor=require(authorization, "education.update")
    try:item=store.save_education(item_id,{**payload.model_dump(mode="json"),"is_published":payload.status=="published"})
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    admin_domain.save_activity(actor,"update","education",item_id,"Memperbarui konten edukasi",new_values={"title":item["title"],"status":item["status"]});return EducationItem(**item)


@router.delete("/education/{item_id}", status_code=204)
def delete_education(item_id: str, authorization: str | None = Header(default=None)) -> None:
    actor=require(authorization, "education.delete")
    if not store.delete_education(item_id): raise HTTPException(404, "Konten tidak ditemukan.")
    admin_domain.save_activity(actor,"archive","education",item_id,"Mengarsipkan konten edukasi")


@router.post("/reports/{report_id}/dataset", response_model=DatasetCandidate, status_code=201)
def process_report(report_id: str, authorization: str | None = Header(default=None)) -> DatasetCandidate:
    admin = require(authorization, "datasets.create")
    report = store.get_report(report_id)
    if not report or report["status"] not in {"reviewed", "approved"}: raise HTTPException(400, "Laporan harus disetujui sebelum masuk dataset.")
    existing = next((item for item in store.candidates() if item.get("report_id") == report_id), None)
    if existing: raise HTTPException(409, "Laporan ini sudah memiliki kandidat dataset.")
    candidate = store.save_candidate(None, {"report_id":report_id,"text_anonymized":anonymize_report(report["text"]),"category":report.get("correct_category") or report["category_suggested"],"source":"community_report","data_type":"primer","validation_status":"pending","split":None,"validator":admin["email"],"notes":report.get("validation_notes"),"is_duplicate":False,"is_archived":False,"nseae_validation":{}})
    store.validate_report(report_id, {"status":"dataset_candidate"})
    # Setelah kandidat anonim terbentuk, isi asli tidak lagi diperlukan oleh MVP.
    store.validate_report(report_id, {"text":"[DIHAPUS SETELAH ANONIMISASI]", "anonymized_text": candidate["text_anonymized"], "reviewer_id": admin["id"], "reviewed_at": datetime.utcnow()})
    store.add_activity(admin["email"], "create_candidate", "dataset_candidate", candidate["id"], report_id)
    return DatasetCandidate(**candidate)

@router.post("/candidates/{candidate_id}/publish", response_model=PublicDatasetRow, status_code=201)
def publish_candidate(candidate_id: str, authorization: str | None = Header(default=None)) -> PublicDatasetRow:
    actor = require(authorization, "datasets.validate")
    row = store.publish_candidate(candidate_id)
    if not row: raise HTTPException(422, "Kandidat harus terverifikasi, bukan duplikat, berasal dari laporan, dan memiliki enam validasi N-SEAE yang pasti.")
    admin_domain.save_activity(actor, "publish", "dataset_candidate", candidate_id, "Mempublikasikan kandidat tervalidasi ke dataset publik")
    return PublicDatasetRow(**row)


@router.get("/candidates", response_model=list[DatasetCandidate])
def candidates(authorization: str | None = Header(default=None)) -> list[DatasetCandidate]:
    require(authorization, "datasets.view")
    return [DatasetCandidate(**item) for item in store.candidates()]


@router.post("/candidates", response_model=DatasetCandidate, status_code=201)
def create_candidate(payload: DatasetCandidateRequest, authorization: str | None = Header(default=None)) -> DatasetCandidate:
    admin=require(authorization,"datasets.create")
    if anonymize_report(payload.text_anonymized) != payload.text_anonymized: raise HTTPException(422, "Teks kandidat masih mengandung data pribadi.")
    item=store.save_candidate(None,{**payload.model_dump(),"validation_status":"pending","validator":payload.validator or admin["email"]});store.add_activity(admin["email"],"create_candidate","dataset_candidate",item["id"]);return DatasetCandidate(**item)


@router.patch("/candidates/{candidate_id}", response_model=DatasetCandidate)
def update_candidate(candidate_id: str, payload: DatasetCandidateRequest, authorization: str | None = Header(default=None)) -> DatasetCandidate:
    admin=require(authorization,"datasets.update")
    if anonymize_report(payload.text_anonymized) != payload.text_anonymized: raise HTTPException(422, "Teks kandidat masih mengandung data pribadi.")
    if payload.validation_status == "verified":
        validations = [item for item in admin_domain.crud_list("nseae_validations") if item["dataset_candidate_id"] == candidate_id and item["human_validation"] != "unsure"]
        if len({item["indicator"] for item in validations}) != 6: raise HTTPException(422, "Status verified memerlukan enam validasi N-SEAE yang pasti.")
    item=store.save_candidate(candidate_id,{**payload.model_dump(),"validator":payload.validator or admin["email"]});store.add_activity(admin["email"],"update_candidate","dataset_candidate",candidate_id);return DatasetCandidate(**item)


@router.delete("/candidates/{candidate_id}", status_code=204)
def archive_candidate(candidate_id: str, authorization: str | None = Header(default=None)) -> None:
    admin=require(authorization,"datasets.archive")
    if not store.archive_candidate(candidate_id):raise HTTPException(404,"Kandidat tidak ditemukan.")
    store.add_activity(admin["email"],"archive_candidate","dataset_candidate",candidate_id)


@router.get("/activities")
def activities(authorization: str | None = Header(default=None)) -> list[dict]:
    require(authorization,"activity_logs.view");return store.activities()


@router.post("/profile/password", status_code=204)
def change_password(payload: PasswordChangeRequest, authorization: str | None = Header(default=None)) -> None:
    admin=require(authorization,"profile.manage")
    if not store.change_password(admin["id"],payload.current_password,payload.new_password):raise HTTPException(400,"Password lama tidak sesuai.")
    store.add_activity(admin["email"],"change_password","admin_profile",admin["id"])


class LexiconPayload(BaseModel):
    phrase: str = Field(min_length=1, max_length=240)
    indicator: str
    weight: float = Field(ge=0, le=1)
    match_type: Literal["exact", "contains", "regex"] = "contains"
    example: str = Field(default="", max_length=1000)
    description: str = Field(default="", max_length=1000)
    is_active: bool = True

class LexiconTestPayload(BaseModel):
    text: str = Field(min_length=1, max_length=5000)

class RecommendationPayload(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    content: str = Field(min_length=10, max_length=3000)
    category: str | None = None
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] | None = None
    nseae_indicator: str | None = None
    display_order: int = Field(default=0, ge=0, le=10000)
    is_active: bool = True

class NseaeValidationRow(BaseModel):
    indicator: str
    ai_score: float = Field(ge=0, le=1)
    human_validation: Literal["detected", "not_detected", "unsure"]
    detected_evidence: str = Field(default="", max_length=1000)
    notes: str = Field(default="", max_length=2000)

class NseaeValidationPayload(BaseModel):
    validations: list[NseaeValidationRow] = Field(min_length=6, max_length=6)

class SettingsPayload(BaseModel):
    values: dict[str, dict[str, str]]

class DatasetImportPayload(BaseModel):
    rows: list[DatasetCandidateRequest] = Field(min_length=1, max_length=5000)

class ModelVersionPayload(BaseModel):
    id: str | None = None
    model_name: str = Field(min_length=2, max_length=120)
    version: str = Field(min_length=1, max_length=80)
    status: Literal["active", "inactive", "archived"] = "inactive"
    accuracy: float | None = Field(default=None, ge=0, le=1)
    precision_score: float | None = Field(default=None, ge=0, le=1)
    recall_score: float | None = Field(default=None, ge=0, le=1)
    f1_score: float | None = Field(default=None, ge=0, le=1)
    evaluation_dataset: str | None = Field(default=None, max_length=240)
    evaluated_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)

class ProfileUpdatePayload(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    avatar: str | None = Field(default=None, max_length=500)

class ImageUploadPayload(BaseModel):
    data_url: str = Field(max_length=3_000_000)
    alt_text: str = Field(min_length=2, max_length=240)

@router.post("/education/upload",status_code=201)
def upload_education_image(payload:ImageUploadPayload,authorization:str|None=Header(default=None))->dict:
    actor=require(authorization,"education.create")
    match=re.fullmatch(r"data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)",payload.data_url)
    if not match:raise HTTPException(422,"Format gambar harus PNG, JPEG, atau WebP.")
    content=base64.b64decode(match.group(2),validate=True)
    if len(content)>2_000_000:raise HTTPException(422,"Ukuran gambar maksimal 2 MB.")
    extension="jpg" if match.group(1)=="jpeg" else match.group(1);name=f"{uuid.uuid4().hex}.{extension}";target=Path("uploads/education")/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
    admin_domain.save_activity(actor,"upload","education",None,"Mengunggah gambar konten yang telah divalidasi")
    return {"url":f"/uploads/education/{name}","alt_text":payload.alt_text}

@router.get("/profile")
def profile(authorization: str | None = Header(default=None)) -> dict:
    actor=require(authorization,"profile.manage");item=admin_domain.user_detail(actor["id"])
    if not item:raise HTTPException(404,"Profil tidak ditemukan.")
    return item

@router.patch("/profile")
def update_profile(payload:ProfileUpdatePayload,authorization:str|None=Header(default=None))->dict:
    actor=require(authorization,"profile.manage");item=admin_domain.update_internal_user(actor["id"],payload.model_dump(),actor);admin_domain.save_activity(actor,"update","profile",actor["id"],"Memperbarui profil sendiri");return item


@router.get("/roles")
def roles(authorization: str | None = Header(default=None)) -> dict:
    require(authorization, "roles.manage")
    return {"roles": admin_domain.roles(), "permissions": admin_domain.permission_catalog()}

@router.get("/roles/assignable")
def assignable_roles(authorization: str | None = Header(default=None)) -> dict:
    require(authorization, "users.view")
    return {"roles": admin_domain.roles()}

@router.post("/roles", status_code=201)
def create_role(payload: RoleRequest, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "roles.manage")
    try: item = admin_domain.save_role(None, payload.model_dump())
    except Exception as exc: raise HTTPException(422, str(exc)) from exc
    admin_domain.save_activity(actor, "create", "roles", item["id"], "Menambahkan role", new_values=item)
    return item

@router.patch("/roles/{role_id}")
def update_role(role_id: str, payload: RoleRequest, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "roles.manage")
    try: item = admin_domain.save_role(role_id, payload.model_dump())
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    admin_domain.save_activity(actor, "update", "roles", role_id, "Memperbarui role dan permission")
    return item

@router.get("/nseae-validations")
def nseae_validation_list(candidate_id: str | None = None, authorization: str | None = Header(default=None)) -> dict:
    require(authorization, "nseae.validate")
    candidates = store.candidates(); validations = admin_domain.crud_list("nseae_validations")
    if candidate_id: candidates = [item for item in candidates if item["id"] == candidate_id]; validations = [item for item in validations if item["dataset_candidate_id"] == candidate_id]
    return {"candidates": candidates, "validations": validations, "indicators": INDICATORS, "validated_count": len({item["dataset_candidate_id"] for item in validations}), "total": len(candidates)}

@router.put("/nseae-validations/{candidate_id}")
def save_nseae_validation(candidate_id: str, payload: NseaeValidationPayload, authorization: str | None = Header(default=None)) -> list[dict]:
    actor = require(authorization, "nseae.validate")
    if {item.indicator for item in payload.validations} != set(INDICATORS): raise HTTPException(422, "Keenam indikator N-SEAE harus diisi tepat satu kali.")
    try: rows = admin_domain.save_nseae_validation(candidate_id, [item.model_dump() for item in payload.validations], actor["id"])
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    admin_domain.save_activity(actor, "validate", "nseae", candidate_id, "Menyimpan validasi manusia terpisah dari skor AI")
    return rows

@router.get("/lexicons")
def lexicons(authorization: str | None = Header(default=None)) -> list[dict]:
    require(authorization, "lexicons.view"); return admin_domain.crud_list("nseae_lexicons")

@router.post("/lexicons", status_code=201)
def create_lexicon(payload: LexiconPayload, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "lexicons.manage")
    try: item = admin_domain.save_lexicon(None, payload.model_dump(), actor["id"])
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    admin_domain.save_activity(actor, "create", "lexicons", item["id"], "Menambahkan leksikon", new_values=item); return item

@router.patch("/lexicons/{item_id}")
def update_lexicon(item_id: str, payload: LexiconPayload, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "lexicons.manage")
    try: item = admin_domain.save_lexicon(item_id, payload.model_dump(), actor["id"])
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    admin_domain.save_activity(actor, "update", "lexicons", item_id, "Memperbarui leksikon"); return item

@router.delete("/lexicons/{item_id}", status_code=204)
def archive_lexicon(item_id: str, authorization: str | None = Header(default=None)) -> None:
    actor = require(authorization, "lexicons.manage")
    if not admin_domain.archive("nseae_lexicons", item_id): raise HTTPException(404, "Leksikon tidak ditemukan.")
    admin_domain.save_activity(actor, "archive", "lexicons", item_id, "Mengarsipkan leksikon")

@router.post("/lexicons/test")
def test_lexicon(payload: LexiconTestPayload, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "lexicons.manage"); matches = admin_domain.test_lexicons(payload.text)
    admin_domain.save_activity(actor, "test", "lexicons", None, "Menguji leksikon tanpa menyimpan teks contoh")
    return {"matches": matches, "detected_indicators": sorted({item["indicator"] for item in matches})}

@router.get("/recommendations")
def recommendations(authorization: str | None = Header(default=None)) -> list[dict]:
    require(authorization, "recommendations.manage"); return admin_domain.crud_list("action_recommendations")

@router.post("/recommendations", status_code=201)
def create_recommendation(payload: RecommendationPayload, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "recommendations.manage"); item = admin_domain.save_recommendation(None, payload.model_dump(), actor["id"]); admin_domain.save_activity(actor, "create", "recommendations", item["id"], "Menambahkan rekomendasi"); return item

@router.patch("/recommendations/{item_id}")
def update_recommendation(item_id: str, payload: RecommendationPayload, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "recommendations.manage"); item = admin_domain.save_recommendation(item_id, payload.model_dump(), actor["id"]); admin_domain.save_activity(actor, "update", "recommendations", item_id, "Memperbarui rekomendasi"); return item

@router.delete("/recommendations/{item_id}", status_code=204)
def archive_recommendation(item_id: str, authorization: str | None = Header(default=None)) -> None:
    actor = require(authorization, "recommendations.manage")
    if not admin_domain.archive("action_recommendations", item_id): raise HTTPException(404, "Rekomendasi tidak ditemukan.")
    admin_domain.save_activity(actor, "archive", "recommendations", item_id, "Mengarsipkan rekomendasi")

@router.get("/statistics")
def internal_statistics(start: str | None = None, end: str | None = None, authorization: str | None = Header(default=None)) -> dict:
    require(authorization, "statistics.view"); return admin_domain.statistics(start, end)

@router.get("/candidates/distribution")
def candidate_distribution(authorization: str | None = Header(default=None)) -> dict:
    require(authorization, "datasets.view"); return admin_domain.candidate_distribution()

@router.post("/candidates/import")
def import_candidates(payload: DatasetImportPayload, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "datasets.import"); imported, failed = [], []
    for index, row in enumerate(payload.rows, start=1):
        data = row.model_dump()
        if anonymize_report(data["text_anonymized"]) != data["text_anonymized"]:
            failed.append({"row": index, "reason": "Teks masih mengandung data pribadi."}); continue
        try: imported.append(store.save_candidate(None, {**data, "validator": data.get("validator") or actor["email"]}))
        except Exception as exc: failed.append({"row": index, "reason": str(exc)[:200]})
    admin_domain.save_activity(actor, "import", "datasets", None, f"Impor kandidat: {len(imported)} berhasil, {len(failed)} gagal")
    return {"imported": len(imported), "failed": failed}

@router.get("/candidates/export")
def export_candidates(category: str | None = None, validation_status: str | None = None, split: str | None = None, authorization: str | None = Header(default=None)) -> Response:
    actor = require(authorization, "datasets.export"); rows = store.candidates()
    rows = [row for row in rows if (not category or row["category"] == category) and (not validation_status or row["validation_status"] == validation_status) and (not split or row["split"] == split)]
    output = io.StringIO(); writer = csv.writer(output); writer.writerow(["text_anonymized", "category", "source", "data_type", "validation_status", "split", "annotation_version"])
    for row in rows: writer.writerow([anonymize_report(row["text_anonymized"]), row["category"], row["source"], row["data_type"], row["validation_status"], row["split"] or "", row.get("annotation_version", "1.0")])
    admin_domain.save_activity(actor, "export", "datasets", None, f"Mengekspor {len(rows)} kandidat anonim")
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=nusaguard-dataset.csv"})

@router.get("/settings")
def settings(authorization: str | None = Header(default=None)) -> dict:
    require(authorization, "settings.manage"); return admin_domain.settings()

@router.put("/settings")
def update_settings(payload: SettingsPayload, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "settings.manage"); item = admin_domain.save_settings(payload.values, actor["id"]); admin_domain.save_activity(actor, "update", "settings", None, "Memperbarui pengaturan sistem"); return item

@router.get("/models")
def models(authorization: str | None = Header(default=None)) -> dict:
    require(authorization, "models.view"); started = time.perf_counter(); pipeline = _pipeline(); latency = (time.perf_counter()-started)*1000
    return {"service_status": "connected", "model_source": "indobert" if pipeline is not None else "rules-fallback", "endpoint": "/api/analyze", "checked_at": datetime.utcnow(), "health_response_ms": round(latency, 2), "versions": admin_domain.model_versions(), "statistics": admin_domain.statistics()}

@router.post("/models/versions", status_code=201)
def create_model_version(payload: ModelVersionPayload, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "models.manage"); item = admin_domain.save_model_version(payload.model_dump()); admin_domain.save_activity(actor, "create_version", "models", item["id"], "Menyimpan metadata versi model"); return item

@router.post("/models/test")
def test_model(payload: AnalyzeRequest, authorization: str | None = Header(default=None)) -> dict:
    actor = require(authorization, "models.test"); started = time.perf_counter(); result = analyze(payload); admin_domain.save_activity(actor, "test", "models", None, "Menguji model; teks tidak disimpan"); return {**result.model_dump(mode="json"), "processing_time_ms": round((time.perf_counter()-started)*1000, 2)}

