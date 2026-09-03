import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from app.models.schemas import KategoriDasar, KategoriNusaGuard
from app.services.nseae import aggregate_nseae_risk, has_protective_context

KEYWORDS = {
    KategoriNusaGuard.PHISHING: (
        "http://", "https://", "klik link", "tautan", ".com", ".xyz",
        ".apk", "undangan digital", "buka foto undangan", "lampirkan undangan",
        "unduh untuk melihat", "download aplikasi",
    ),
    KategoriNusaGuard.PENIPUAN_INVESTASI: ("investasi", "profit", "cuan", "return", "trading", "passive income", "hasil pasti", "keuntungan tanpa", "robot trading", "kripto rahasia"),
    KategoriNusaGuard.PENIPUAN_REKRUTMEN: ("lowongan", "rekrut", "hrd", "kerja paruh waktu", "biaya administrasi", "interview", "biaya seragam", "medical check-up", "tugas online", "kursi kerja"),
    KategoriNusaGuard.PENIPUAN_ROMANSA: ("sayang", "cinta", "jodoh", "kirim uang", "butuh bantuan", "hubungan kita", "menikah denganmu", "menemuimu", "hadiah pernikahan", "bea cukai", "cintaku"),
    KategoriNusaGuard.SOCIAL_ENGINEERING: ("otp", "pin", "password", "rekening", "diblokir", "petugas", "kode verifikasi", "data pribadi", "foto kartu", "nomor baru", "transfer darurat", "customer service", "pihak berwenang"),
}


def _contains_term(text: str, term: str) -> bool:
    if any(character in term for character in ":/.["):
        return term in text
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) is not None


def _has_explicit_scam_signal(text: str) -> bool:
    normalized = text.casefold()
    strong_patterns = (
        r"https?://|\.apk\b|\.zip\b",
        r"\b(?:kirim|minta|sebutkan|masukkan|berikan)\b.{0,35}\b(?:otp|pin|password|kata sandi|kode verifikasi)\b",
        r"\b(?:kirim|transfer|pinjamkan|bayar|setor|deposit|top up)\b.{0,35}\b(?:uang|dana|rp\.?\s?\d|biaya|saldo|modal)\b",
        r"\b(?:profit|return|keuntungan|cuan)\b.{0,35}\b(?:pasti|dijamin|tanpa risiko|per hari|per minggu)\b",
    )
    return any(re.search(pattern, normalized) for pattern in strong_patterns)

@lru_cache(maxsize=1)
def _pipeline():
    default_path = Path(__file__).resolve().parents[2] / "model" / "indobert"
    model_path = Path(os.getenv("NUSAGUARD_MODEL_PATH", str(default_path)))
    if not (model_path / "config.json").exists():
        model_repo = os.getenv("NUSAGUARD_MODEL_REPO", "indobenchmark/indobert-base-p1")
        try:
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id=model_repo,
                revision=os.getenv("NUSAGUARD_MODEL_REVISION", "main"),
                local_dir=model_path,
                local_dir_use_symlinks=False
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("Failed to download model from %s: %s", model_repo, e)
            return None
    from transformers import pipeline
    return pipeline("text-classification", model=str(model_path), tokenizer=str(model_path), top_k=1)

def predict_probabilities(text: str) -> tuple[dict[KategoriNusaGuard, float] | None, str]:
    classifier = _pipeline()
    if not classifier:
        return None, "rules-fallback"
    rows = classifier(text, truncation=True, max_length=256, top_k=None)
    return {KategoriNusaGuard(row["label"]): float(row["score"]) for row in rows}, "indobert"


def predict_category(text: str) -> tuple[KategoriDasar, KategoriNusaGuard, float, str]:
    probabilities, source = predict_probabilities(text)
    normalized = text.casefold()
    if probabilities:
        label, confidence = max(probabilities.items(), key=lambda item: item[1])
        # Critical, explicit indicators remain deterministic safety guards around
        # the learned model, particularly while training data is still synthetic.
        if ".apk" in normalized or "http://" in normalized or "https://" in normalized:
            label = KategoriNusaGuard.PHISHING
        elif any(term in normalized for term in ("kirim otp", "minta otp", "kirim pin", "minta pin", "kirim password", "minta password")):
            label = KategoriNusaGuard.SOCIAL_ENGINEERING
        return (KategoriDasar.HAM if label is KategoriNusaGuard.AMAN else KategoriDasar.SPAM, label, confidence, source)
    label, count = max(((label, sum(_contains_term(normalized, term) for term in terms)) for label, terms in KEYWORDS.items()), key=lambda item: item[1])
    if count == 0:
        return KategoriDasar.HAM, KategoriNusaGuard.AMAN, 0.65, "rules-fallback"
    return KategoriDasar.SPAM, label, min(0.60 + count * 0.10, 0.90), "rules-fallback"


def predict_category_with_fusion(text: str, nseae_scores: dict[str, float]) -> tuple[KategoriDasar, KategoriNusaGuard, float, str, bool, float]:
    tokens = re.findall(r"\b\w+\b", text.casefold())
    risk = aggregate_nseae_risk(nseae_scores)
    if len(tokens) <= 5 and risk == 0 and not _has_explicit_scam_signal(text):
        return KategoriDasar.HAM, KategoriNusaGuard.AMAN, 0.65, "low-information-guard", True, 0.0
    probabilities, source = predict_probabilities(text)
    if not probabilities:
        basic, label, confidence, fallback_source = predict_category(text)
        normalized = text.casefold()
        active_indicators = sum(score > 0 for score in nseae_scores.values())
        if label is not KategoriNusaGuard.AMAN and has_protective_context(text) and ".apk" not in normalized and "http://" not in normalized and "https://" not in normalized and (risk < 0.50 or active_indicators <= 1):
            return KategoriDasar.HAM, KategoriNusaGuard.AMAN, round(max(1.0 - risk, 0.65), 4), "rules-fallback+nseae", True, confidence
        return basic, label, confidence, fallback_source, False, confidence

    baseline_label, model_confidence = max(probabilities.items(), key=lambda item: item[1])
    label, fusion_applied = baseline_label, False
    normalized = text.casefold()
    active_indicators = sum(score > 0 for score in nseae_scores.values())
    if baseline_label is not KategoriNusaGuard.AMAN and risk == 0 and not _has_explicit_scam_signal(text):
        label, fusion_applied = KategoriNusaGuard.AMAN, True
    elif baseline_label is not KategoriNusaGuard.AMAN and has_protective_context(text) and (risk < 0.50 or active_indicators <= 1):
        label, fusion_applied = KategoriNusaGuard.AMAN, True
    elif ".apk" in normalized or "http://" in normalized or "https://" in normalized:
        label, fusion_applied = KategoriNusaGuard.PHISHING, baseline_label is not KategoriNusaGuard.PHISHING
    elif any(term in normalized for term in ("kirim otp", "minta otp", "kirim pin", "minta pin", "kirim password", "minta password")):
        label, fusion_applied = KategoriNusaGuard.SOCIAL_ENGINEERING, baseline_label is not KategoriNusaGuard.SOCIAL_ENGINEERING
    elif baseline_label is KategoriNusaGuard.AMAN and risk >= 0.55:
        suspicious = {candidate: score for candidate, score in probabilities.items() if candidate is not KategoriNusaGuard.AMAN}
        label = max(suspicious.items(), key=lambda item: item[1])[0]
        fusion_applied = True

    if label is baseline_label:
        confidence = min(1.0, 0.85 * model_confidence + 0.15 * risk) if label is not KategoriNusaGuard.AMAN else model_confidence
    elif label is KategoriNusaGuard.AMAN and fusion_applied:
        confidence = max(probabilities[label], 1.0 - risk)
    else:
        confidence = max(probabilities[label], risk * 0.75)
    basic = KategoriDasar.HAM if label is KategoriNusaGuard.AMAN else KategoriDasar.SPAM
    return basic, label, round(confidence, 4), "indobert+nseae", fusion_applied, model_confidence

