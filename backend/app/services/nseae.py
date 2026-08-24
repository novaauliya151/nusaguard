import re

from app.models.schemas import DetectedPattern


# This is deliberately small and deterministic while the trained N-SEAE model is
# not available. Each indicator is emitted only when its lexicon matches.
INDICATORS: dict[str, tuple[float, tuple[str, ...]]] = {
    "urgency": (0.30, (r"\bsegera\b", r"\bsekarang\b", r"\bhari ini\b", r"\bbatas waktu\b")),
    "authority": (0.25, (r"\bpolisi\b", r"\bbank\b", r"\bkantor pusat\b", r"\bpetugas\b")),
    "fear": (0.20, (r"\bdiblokir\b", r"\bditangkap\b", r"\bdenda\b", r"\bbermasalah\b")),
    "reward": (0.20, (r"\bhadiah\b", r"\bbonus\b", r"\bmenang\b", r"\bgratis\b")),
    "impersonation": (0.15, (r"\bsaya dari\b", r"\batas nama\b", r"\bmengaku\b")),
    "credential_request": (
        0.40,
        (r"\botp\b", r"\bpin\b", r"\bpassword\b", r"\bkata sandi\b", r"\bnomor rekening\b"),
    ),
}


def analyze_nseae(text: str) -> list[DetectedPattern]:
    normalized = text.casefold()
    return [
        DetectedPattern(pattern=name, weight=weight)
        for name, (weight, patterns) in INDICATORS.items()
        if any(re.search(pattern, normalized) for pattern in patterns)
    ]
