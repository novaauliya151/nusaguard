from app.api.routes.analyze import score_to_risk_level
from app.models.schemas import RiskLevel
from app.services.explanation import generate_explanation
from app.services.nseae import analyze_nseae


def test_benign_message_has_no_indicators() -> None:
    patterns = analyze_nseae("Besok kita makan siang bersama di kantin.")

    assert patterns == []
    assert generate_explanation(patterns, "Aman").startswith("Tidak ada indikator")


def test_suspicious_message_only_returns_matching_indicators() -> None:
    patterns = analyze_nseae("Segera kirim OTP sekarang, atau rekening Anda diblokir!")
    names = {pattern.pattern for pattern in patterns}
    score = sum(pattern.weight or 0 for pattern in patterns)

    assert names == {"urgency", "fear", "credential_request"}
    assert score_to_risk_level(score) is RiskLevel.HIGH


def test_reward_alone_does_not_create_high_risk() -> None:
    patterns = analyze_nseae("Nikmati bonus internet gratis untuk pelanggan.")
    score = sum(pattern.weight or 0 for pattern in patterns)

    assert {pattern.pattern for pattern in patterns} == {"reward"}
    assert score_to_risk_level(score) is RiskLevel.LOW
