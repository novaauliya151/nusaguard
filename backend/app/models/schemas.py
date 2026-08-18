"""
backend/app/models/schemas.py

Kontrak data antara:
- Dataset (Kategori, Pesan, Kategori_NusaGuard)
- Model AI (IndoBERT + N-SEAE)
- API response ke client (Next.js / Flutter)
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# 1. TAKSONOMI LABEL (harus sama persis dengan dataset CSV)
# ---------------------------------------------------------

class KategoriDasar(str, Enum):
    """Label biner awal, sesuai kolom 'Kategori' di dataset mentah."""
    SPAM = "spam"
    HAM = "ham"


class KategoriNusaGuard(str, Enum):
    """
    Label spesifik jenis modus, sesuai kolom 'Kategori_NusaGuard'.
    Kalau nanti nambah kategori baru, cukup tambah di sini —
    tapi ingat: model harus di-retrain ulang kalau jumlah kelas berubah.
    """
    AMAN = "Aman"
    PHISHING = "Phishing/Link Berbahaya"
    SOCIAL_ENGINEERING = "Social Engineering"
    PENIPUAN_INVESTASI = "Penipuan Investasi"
    PENIPUAN_REKRUTMEN = "Penipuan Rekrutmen"
    PENIPUAN_ROMANSA = "Penipuan Romansa"


class RiskLevel(str, Enum):
    """Level risiko akhir yang ditampilkan ke user (hasil scoring N-SEAE)."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ---------------------------------------------------------
# 2. REQUEST SCHEMA — POST /api/analyze
# ---------------------------------------------------------

class AnalyzeRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Teks pesan yang mau dianalisis (dari WhatsApp/SMS/dsb)",
        examples=["Selamat Anda mendapatkan hadiah Rp10.000.000. Klik link ini sekarang!"],
    )
    source: Optional[str] = Field(
        default=None,
        description="Asal pesan, opsional. Misal: 'whatsapp', 'sms', 'manual_web'",
    )


# ---------------------------------------------------------
# 3. RESPONSE SCHEMA — hasil dari IndoBERT + N-SEAE
# ---------------------------------------------------------

class DetectedPattern(BaseModel):
    """Satu pola/indikator yang terdeteksi di dalam pesan."""
    pattern: str = Field(..., examples=["urgency", "reward", "suspicious_link"])
    weight: Optional[float] = Field(
        default=None, description="Kontribusi pola ini terhadap risk_score"
    )


class AnalyzeResponse(BaseModel):
    kategori_dasar: KategoriDasar
    kategori_nusaguard: KategoriNusaGuard
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence model IndoBERT terhadap prediksi ini"
    )
    detected_patterns: List[DetectedPattern] = []
    explanation: str = Field(
        ..., description="Penjelasan human-readable kenapa pesan ini diberi label tsb"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "kategori_dasar": "spam",
                "kategori_nusaguard": "Social Engineering",
                "risk_level": "HIGH",
                "risk_score": 0.94,
                "confidence": 0.91,
                "detected_patterns": [
                    {"pattern": "urgency", "weight": 0.3},
                    {"pattern": "reward", "weight": 0.25},
                    {"pattern": "suspicious_link", "weight": 0.39},
                ],
                "explanation": "Pesan menggunakan iming-iming hadiah dan tekanan waktu untuk mendorong pengguna segera melakukan tindakan.",
            }
        }


# ---------------------------------------------------------
# 4. SCHEMA UNTUK DATASET ROW (dipakai saat preprocessing)
# ---------------------------------------------------------

class DatasetRow(BaseModel):
    """Satu baris dataset processed. Dipakai untuk validasi sebelum training."""
    kategori: KategoriDasar
    pesan: str
    kategori_nusaguard: KategoriNusaGuard