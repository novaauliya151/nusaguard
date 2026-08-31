from fastapi import APIRouter, Header, HTTPException
from app.api.routes.auth import bearer_user
from app.api.routes.content import anonymize_report
from app.models.schemas import ReportRequest, ReportResponse
from app.services.store import admin_domain, store
from app.services.nseae import aggregate_nseae_risk, analyze_nseae
from app.services.predictor import predict_category_with_fusion

router = APIRouter(tags=["reports"])

@router.post("/report", response_model=ReportResponse, status_code=201)
def create_report(payload: ReportRequest, authorization: str | None = Header(default=None)) -> ReportResponse:
    if not admin_domain.setting_enabled("reports", "form_enabled", True):
        raise HTTPException(503, "Formulir laporan sedang dinonaktifkan oleh administrator.")
    if not payload.consent:
        raise HTTPException(400, "Persetujuan diperlukan untuk menyimpan laporan secara sukarela.")
    user_id = bearer_user(authorization)["id"] if authorization else None
    report_id, created_at = store.report(payload.text, payload.category_suggested.value, payload.source, payload.additional_notes, user_id, anonymize_report(payload.text))
    _, scores = analyze_nseae(payload.text, admin_domain.active_lexicons())
    _, predicted, confidence, _, _, _ = predict_category_with_fusion(payload.text, scores)
    store.validate_report(report_id, {"predicted_category": predicted.value, "risk_score": aggregate_nseae_risk(scores), "confidence_score": confidence, "nseae_scores": __import__("json").dumps(scores), "updated_at": created_at})
    return ReportResponse(id=report_id, created_at=created_at)
