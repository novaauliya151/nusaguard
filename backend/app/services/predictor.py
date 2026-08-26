import os
import re
from functools import lru_cache
from pathlib import Path
from app.models.schemas import KategoriDasar, KategoriNusaGuard

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

@lru_cache(maxsize=1)
def _pipeline():
    model_path = Path(os.getenv("NUSAGUARD_MODEL_PATH", "model/indobert"))
    if not (model_path / "config.json").exists():
        return None
    from transformers import pipeline
    return pipeline("text-classification", model=str(model_path), tokenizer=str(model_path), top_k=1)

def predict_category(text: str) -> tuple[KategoriDasar, KategoriNusaGuard, float, str]:
    classifier = _pipeline()
    if classifier:
        result = classifier(text, truncation=True, max_length=256)[0][0]
        label = KategoriNusaGuard(result["label"])
        return (KategoriDasar.HAM if label is KategoriNusaGuard.AMAN else KategoriDasar.SPAM, label, float(result["score"]), "indobert")
    normalized = text.casefold()
    label, count = max(((label, sum(_contains_term(normalized, term) for term in terms)) for label, terms in KEYWORDS.items()), key=lambda item: item[1])
    if count == 0:
        return KategoriDasar.HAM, KategoriNusaGuard.AMAN, 0.65, "rules-fallback"
    return KategoriDasar.SPAM, label, min(0.60 + count * 0.10, 0.90), "rules-fallback"
