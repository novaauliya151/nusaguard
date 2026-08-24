from app.models.schemas import DetectedPattern

def generate_explanation(patterns: list[DetectedPattern], kategori: str) -> str:
    if not patterns:
        return "Tidak ada indikator rekayasa sosial yang terdeteksi dalam pesan."

    detected = ", ".join(pattern.pattern for pattern in patterns)
    return f"Pesan terdeteksi memiliki indikator: {detected}."
