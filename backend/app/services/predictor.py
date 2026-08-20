from app.models.schemas import KategoriDasar, KategoriNusaGuard

def predict_category(text: str) -> tuple[KategoriDasar, KategoriNusaGuard, float]:
    # TODO Hari 2-4: ganti dengan inference IndoBERT fine-tuned asli
    return KategoriDasar.SPAM, KategoriNusaGuard.SOCIAL_ENGINEERING, 0.91