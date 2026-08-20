from app.models.schemas import DetectedPattern

def generate_explanation(patterns: list[DetectedPattern], kategori: str) -> str:
    # TODO: ganti dengan generasi penjelasan berbasis pattern asli
    return (
        "Pesan menggunakan tekanan waktu dan permintaan data OTP "
        "yang menyerupai modus social engineering."
    )