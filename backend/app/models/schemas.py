from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

MessageText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]

class KategoriDasar(str, Enum):
    SPAM = "spam"
    HAM = "ham"

class KategoriNusaGuard(str, Enum):
    AMAN = "Aman"
    PHISHING = "Phishing/Link Berbahaya"
    SOCIAL_ENGINEERING = "Social Engineering"
    PENIPUAN_INVESTASI = "Penipuan Investasi"
    PENIPUAN_REKRUTMEN = "Penipuan Rekrutmen"
    PENIPUAN_ROMANSA = "Penipuan Romansa"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    text: MessageText = Field(alias="message", description="Teks diproses sementara dan tidak disimpan")
    source: str | None = Field(default=None, max_length=30)

class DetectedPattern(BaseModel):
    pattern: str
    weight: float = Field(ge=0, le=1)

class AnalyzeResponse(BaseModel):
    kategori_dasar: KategoriDasar
    category: KategoriNusaGuard
    risk_level: RiskLevel
    risk_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    nseae_scores: dict[str, float]
    detected_patterns: list[DetectedPattern] = Field(default_factory=list)
    explanation: str
    recommendation: str
    model_source: str

class CategoryInfo(BaseModel):
    slug: str
    name: KategoriNusaGuard
    description: str
    examples: list[str]
    prevention: list[str]

class ReportRequest(BaseModel):
    text: MessageText
    category_suggested: KategoriNusaGuard
    consent: bool

class ReportResponse(BaseModel):
    id: str
    created_at: datetime

class StatsResponse(BaseModel):
    total_analyzed: int
    category_counts: dict[str, int]

class AdminReport(BaseModel):
    id: str
    text: str
    category_suggested: KategoriNusaGuard
    status: Literal["pending", "reviewed", "rejected"]
    created_at: datetime

class AdminReportUpdate(BaseModel):
    status: Literal["reviewed", "rejected"]

class AdminDashboardResponse(BaseModel):
    total_analyzed: int
    category_counts: dict[str, int]
    reports_total: int
    reports_pending: int
    recent_reports: list[AdminReport]
    model_status: str
    privacy_mode: str

class DatasetRow(BaseModel):
    kategori: KategoriDasar
    pesan: str
    kategori_nusaguard: KategoriNusaGuard

