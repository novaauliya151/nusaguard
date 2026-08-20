from fastapi import APIRouter
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, RiskLevel
from app.services.predictor import predict_category
from app.services.nseae import analyze_nseae
from app.services.explanation import generate_explanation

router = APIRouter()

def score_to_risk_level(score: float) -> RiskLevel:
    if score >= 0.7:
        return RiskLevel.HIGH
    if score >= 0.4:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest):
    kategori_dasar, kategori_nusaguard, confidence = predict_category(payload.message)
    patterns = analyze_nseae(payload.message)
    risk_score = sum(p.weight or 0 for p in patterns)
    explanation = generate_explanation(patterns, kategori_nusaguard.value)

    return AnalyzeResponse(
        kategori_dasar=kategori_dasar,
        kategori_nusaguard=kategori_nusaguard,
        risk_level=score_to_risk_level(risk_score),
        risk_score=round(min(risk_score, 1.0), 2),
        confidence=confidence,
        detected_patterns=patterns,
        explanation=explanation,
    )