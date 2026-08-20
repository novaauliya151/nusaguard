from app.models.schemas import DetectedPattern

NSEAE_INDICATORS = [
    "urgency", "authority", "fear",
    "reward", "impersonation", "credential_request",
]

def analyze_nseae(text: str) -> list[DetectedPattern]:
    # TODO Hari 3: ganti dengan lexicon-based scoring asli
    # Mock: selalu kembalikan 6 indikator, sebagian dengan weight 0
    mock_weights = {
        "urgency": 0.3, "authority": 0.25, "fear": 0.2,
        "reward": 0.0, "impersonation": 0.15, "credential_request": 0.39,
    }
    return [
        DetectedPattern(pattern=p, weight=mock_weights[p])
        for p in NSEAE_INDICATORS
    ]