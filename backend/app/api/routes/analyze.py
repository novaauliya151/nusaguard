from fastapi import APIRouter
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, RiskLevel
from app.services.explanation import generate_explanation, recommendation_for
from app.services.nseae import analyze_nseae
from app.services.predictor import predict_category
from app.services.store import store

router = APIRouter(tags=["analysis"])

def score_to_risk_level(score: float) -> RiskLevel:
    if score >= 0.7:
        return RiskLevel.HIGH
    if score >= 0.4:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    basic, category, confidence, model_source = predict_category(payload.text)
    patterns, scores = analyze_nseae(payload.text)
    risk_score = round(min(sum(scores.values()), 1.0), 2)
    level = score_to_risk_level(risk_score)
    store.increment(category.value)
    return AnalyzeResponse(kategori_dasar=basic, category=category, risk_level=level, risk_score=risk_score, confidence=confidence, nseae_scores=scores, detected_patterns=patterns, explanation=generate_explanation(patterns, category.value), recommendation=recommendation_for(level), model_source=model_source)
