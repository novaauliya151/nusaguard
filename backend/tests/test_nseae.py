from app.api.routes.analyze import score_to_risk_level
from app.models.schemas import RiskLevel
from app.services.explanation import generate_explanation
from app.services.nseae import aggregate_nseae_risk, analyze_nseae, has_protective_context

def test_benign_message_has_no_indicators() -> None:
    patterns, scores = analyze_nseae("Besok kita makan siang bersama di kantin.")
    assert patterns == []
    assert all(score == 0 for score in scores.values())
    assert generate_explanation(patterns, "Aman").startswith("Tidak ditemukan")

def test_suspicious_message_is_high_risk() -> None:
    patterns, scores = analyze_nseae("Segera kirim OTP sekarang, atau rekening Anda diblokir!")
    assert {p.pattern for p in patterns} == {"urgency", "fear", "credential_request"}
    assert score_to_risk_level(aggregate_nseae_risk(scores)) is RiskLevel.HIGH

def test_reward_alone_is_low_risk() -> None:
    patterns, scores = analyze_nseae("Nikmati bonus internet gratis untuk pelanggan.")
    assert {p.pattern for p in patterns} == {"reward"}
    assert score_to_risk_level(aggregate_nseae_risk(scores)) is RiskLevel.LOW

def test_multiple_signals_raise_indicator_intensity() -> None:
    _, one = analyze_nseae("Segera periksa pesan ini.")
    _, several = analyze_nseae("Segera, sekarang juga, jangan ditunda dalam 10 menit.")
    assert several["urgency"] > one["urgency"]

def test_protective_context_is_recognized() -> None:
    assert has_protective_context("Jangan pernah kirim OTP kepada siapa pun.")
    assert has_protective_context("Lowongan ini tanpa biaya pendaftaran.")
    assert not has_protective_context("Kirim OTP sekarang agar akun tidak diblokir.")

