from app.models.schemas import KategoriNusaGuard
from app.services.predictor import _pipeline, predict_category


def test_pin_does_not_match_inside_regular_word(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("NUSAGUARD_MODEL_PATH", str(tmp_path / "missing-model"))
    _pipeline.cache_clear()
    try:
        _, category, _, source = predict_category("Jadwal konsultasi dipindah ke hari Rabu.")
        assert source == "rules-fallback"
        assert category is KategoriNusaGuard.AMAN
    finally:
        _pipeline.cache_clear()


def test_representative_fraud_categories() -> None:
    cases = {
        "Profit investasi 30 persen tanpa risiko": KategoriNusaGuard.PENIPUAN_INVESTASI,
        "HRD meminta biaya administrasi sebelum interview": KategoriNusaGuard.PENIPUAN_REKRUTMEN,
        "Sayang, hadiah pernikahan tertahan di bea cukai": KategoriNusaGuard.PENIPUAN_ROMANSA,
        "Petugas meminta kode verifikasi dan OTP": KategoriNusaGuard.SOCIAL_ENGINEERING,
    }
    for message, expected in cases.items():
        assert predict_category(message)[1] is expected

