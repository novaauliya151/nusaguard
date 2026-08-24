from app.api.routes.analyze import score_to_risk_level
from app.models.schemas import RiskLevel
from app.services.explanation import generate_explanation
from app.services.nseae import analyze_nseae

def test_benign_message_has_no_indicators() -> None:
    patterns, scores = analyze_nseae("Besok kita makan siang bersama di kantin.")
    assert patterns == []
    assert all(score == 0 for score in scores.values())
    assert generate_explanation(patterns, "Aman").startswith("Tidak ditemukan")

def test_suspicious_message_is_high_risk() -> None:
    patterns, scores = analyze_nseae("Segera kirim OTP sekarang, atau rekening Anda diblokir!")
    assert {p.pattern for p in patterns} == {"urgency", "fear", "credential_request"}
    assert score_to_risk_level(sum(scores.values())) is RiskLevel.HIGH

def test_reward_alone_is_low_risk() -> None:
    patterns, scores = analyze_nseae("Nikmati bonus internet gratis untuk pelanggan.")
    assert {p.pattern for p in patterns} == {"reward"}
    assert score_to_risk_level(sum(scores.values())) is RiskLevel.LOW
