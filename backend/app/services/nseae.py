import re
from app.models.schemas import DetectedPattern

INDICATORS: dict[str, tuple[float, tuple[str, ...]]] = {
    "urgency": (0.30, (r"\bsegera\b", r"\bsekarang\b", r"\bhari ini\b", r"\bbatas waktu\b", r"\bburuan\b")),
    "authority": (0.20, (r"\bpolisi\b", r"\bbank\b", r"\bkantor pusat\b", r"\bpetugas\b", r"\bkominfo\b")),
    "fear": (0.20, (r"\bdiblokir\b", r"\bditangkap\b", r"\bdenda\b", r"\bbermasalah\b", r"\bdinonaktifkan\b")),
    "reward": (0.20, (r"\bhadiah\b", r"\bbonus\b", r"\bmenang\b", r"\bgratis\b", r"\bkomisi\b")),
    "impersonation": (0.15, (r"\bsaya dari\b", r"\batas nama\b", r"\bmengaku\b", r"\badmin\b")),
    "credential_request": (0.40, (r"\botp\b", r"\bpin\b", r"\bpassword\b", r"\bkata sandi\b", r"\bnomor rekening\b", r"\.apk\b")),
}

def analyze_nseae(text: str) -> tuple[list[DetectedPattern], dict[str, float]]:
    normalized = text.casefold()
    scores = {name: weight if any(re.search(pattern, normalized) for pattern in patterns) else 0.0 for name, (weight, patterns) in INDICATORS.items()}
    return [DetectedPattern(pattern=name, weight=score) for name, score in scores.items() if score], scores
