from app.models.schemas import DetectedPattern, RiskLevel

LABELS = {"urgency": "tekanan untuk bertindak segera", "authority": "klaim otoritas", "fear": "ancaman atau rasa takut", "reward": "iming-iming hadiah", "impersonation": "indikasi penyamaran identitas", "credential_request": "permintaan kredensial sensitif"}

def generate_explanation(patterns: list[DetectedPattern], category: str) -> str:
    if not patterns:
        return f"Tidak ditemukan pola rekayasa sosial yang kuat; klasifikasi sementara: {category}."
    return "Terdeteksi " + ", ".join(LABELS[p.pattern] for p in patterns) + "."

def recommendation_for(level: RiskLevel, dynamic: str | None = None) -> str:
    if dynamic:
        return dynamic
    if level is RiskLevel.HIGH:
        return "Jangan klik tautan, jangan kirim OTP/PIN, dan verifikasi pengirim melalui kanal resmi."
    if level is RiskLevel.MEDIUM:
        return "Tunda tindakan dan periksa identitas pengirim serta alamat tautan secara mandiri."
    return "Tetap waspada dan jangan membagikan data sensitif meskipun pesan terlihat aman."
