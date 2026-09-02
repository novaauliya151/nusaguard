import math
import re

from app.models.schemas import DetectedPattern

INDICATORS: dict[str, tuple[tuple[str, float], ...]] = {
    "urgency": (
        (r"\bsegera(?:lah)?\b", 0.38), (r"\bsekarang(?: juga)?\b", 0.42),
        (r"\bhari ini\b", 0.24), (r"\bbatas waktu\b", 0.34),
        (r"\b(?:buruan|cepat|jangan ditunda|kesempatan terakhir)\b", 0.38),
        (r"\bdalam \d+ (?:menit|jam)\b", 0.46),
    ),
    "authority": (
        (r"\b(?:polisi|kepolisian|kominfo|kejaksaan|bea cukai)\b", 0.38),
        (r"\b(?:bank|bri|bca|bni|mandiri|bpjs|pln|pajak)\b", 0.30),
        (r"\b(?:petugas|kantor pusat|pihak berwenang|customer service|cs resmi)\b", 0.32),
        (r"\b(?:surat resmi|nomor perkara|nomor tiket)\b", 0.24),
    ),
    "fear": (
        (r"\b(?:di)?blokir\b", 0.46), (r"\b(?:di)?tangkap\b", 0.48),
        (r"\b(?:denda|pidana|diproses hukum)\b", 0.42),
        (r"\b(?:dinonaktifkan|ditutup permanen|disita)\b", 0.44),
        (r"\b(?:bermasalah|aktivitas mencurigakan|pelanggaran)\b", 0.30),
    ),
    "reward": (
        (r"\b(?:hadiah|bonus|menang|pemenang)\b", 0.36),
        (r"\b(?:gratis|komisi|cashback|cuan)\b", 0.28),
        (r"\b(?:profit|return|keuntungan)\b", 0.32),
        (r"\b(?:tanpa risiko|pasti untung|penghasilan harian)\b", 0.44),
        (r"(?:rp\.?\s?|idr\s?)\d[\d.,]*(?:\s?(?:juta|miliar))?", 0.24),
    ),
    "impersonation": (
        (r"\b(?:saya|kami) dari\b", 0.38), (r"\batas nama\b", 0.34),
        (r"\b(?:mengaku|perwakilan resmi|admin resmi)\b", 0.38),
        (r"\b(?:nomor baru saya|ini mama|ini papa|teman lama)\b", 0.42),
        (r"\b(?:cs|customer service)\s+[a-z0-9]+", 0.36),
    ),
    "credential_request": (
        (r"\b(?:kirim|sebutkan|masukkan|konfirmasi|berikan|foto)\b.{0,30}\botp\b", 0.72),
        (r"\b(?:kirim|sebutkan|masukkan|konfirmasi|berikan)\b.{0,30}\bpin\b", 0.70),
        (r"\b(?:kirim|masukkan|konfirmasi|berikan)\b.{0,30}\b(?:password|kata sandi)\b", 0.70),
        (r"\b(?:foto|kirim|unggah)\b.{0,30}\b(?:ktp|kartu atm|buku tabungan)\b", 0.62),
        (r"\b(?:nomor rekening|kode verifikasi|data pribadi|nik)\b", 0.42),
        (r"\.apk\b", 0.68),
    ),
}

RISK_IMPORTANCE = {"urgency": 0.25, "authority": 0.20, "fear": 0.25, "reward": 0.20, "impersonation": 0.20, "credential_request": 0.45}

PROTECTIVE_CONTEXT = (
    r"\bjangan pernah (?:kirim|bagikan|berikan)\b",
    r"\b(?:otp|pin|kata sandi|password) tidak pernah (?:diminta|boleh dibagikan)\b",
    r"\b(?:tanpa|tidak ada) biaya\b",
    r"\b(?:sudah|telah) otomatis (?:masuk|aktif)\b",
    r"\bmelalui (?:situs|laman|aplikasi) resmi\b",
    r"\bseminar|edukasi|literasi digital\b",
)


def _indicator_score(text: str, signals: tuple[tuple[str, float], ...]) -> float:
    matched = [weight for pattern, weight in signals if re.search(pattern, text, re.DOTALL)]
    if not matched:
        return 0.0
    return round(min(1.0 - math.prod(1.0 - weight for weight in matched), 1.0), 3)


def aggregate_nseae_risk(scores: dict[str, float]) -> float:
    active = sum(score > 0 for score in scores.values())
    weighted = sum(scores[name] * RISK_IMPORTANCE[name] for name in RISK_IMPORTANCE)
    synergy = max(active - 1, 0) * 0.12
    credential_synergy = 0.20 if scores.get("credential_request", 0) >= 0.55 and active >= 2 else 0.0
    return round(min(weighted + synergy + credential_synergy, 1.0), 3)


def has_protective_context(text: str) -> bool:
    normalized = " ".join(text.casefold().split())
    return any(re.search(pattern, normalized) for pattern in PROTECTIVE_CONTEXT)


def analyze_nseae(text: str, lexicons: list[dict] | None = None) -> tuple[list[DetectedPattern], dict[str, float]]:
    normalized = " ".join(text.casefold().split())
    signals = {name: list(items) for name, items in INDICATORS.items()}
    for item in lexicons or []:
        phrase, kind = item["phrase"], item["match_type"]
        pattern = phrase if kind == "regex" else rf"\b{re.escape(phrase)}\b" if kind == "exact" else re.escape(phrase)
        signals.setdefault(item["indicator"], []).append((pattern, float(item["weight"])))
    scores = {name: _indicator_score(normalized, tuple(items)) for name, items in signals.items()}
    return [DetectedPattern(pattern=name, weight=score) for name, score in scores.items() if score], scores

