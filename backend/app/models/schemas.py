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
    model_confidence: float = Field(ge=0, le=1)
    nseae_risk_score: float = Field(ge=0, le=1)
    fusion_applied: bool
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
    month_total: int
    month_category_counts: dict[str, int]
    top_category_this_month: str | None
    daily_stats: list[dict[str, object]]
    updated_at: datetime

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
    daily_stats: list[dict[str, object]]
    source_counts: dict[str, int]
    database_engine: str
    database_connected: bool

class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    role: Literal["user", "analyst", "moderator", "admin"]
    permissions: list[str]
    is_active: bool
    created_at: datetime

class RegisterRequest(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=160, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)]

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic

class UserCreateRequest(RegisterRequest):
    role: Literal["user", "analyst", "moderator", "admin"] = "user"

class UserUpdateRequest(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)] | None = None
    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=160, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")] | None = None
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)] | None = None
    role: Literal["user", "analyst", "moderator", "admin"] | None = None
    is_active: bool | None = None

class EducationItemRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=120)]
    category: KategoriNusaGuard
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=1000)]
    warning_signs: list[str] = Field(min_length=1, max_length=10)
    prevention: list[str] = Field(min_length=1, max_length=10)
    is_published: bool = True

class EducationItem(EducationItemRequest):
    id: str
    created_at: datetime
    updated_at: datetime

class PublicDatasetRow(BaseModel):
    id: str
    text_anonymized: str
    category: KategoriNusaGuard
    provenance: str
    reviewed: bool
    created_at: datetime

class DatasetCollectionInfo(BaseModel):
    public_samples: int
    development_samples: int
    development_categories: int
    development_samples_per_category: int
    public_collection: str
    development_collection: str
    development_downloadable: bool

class DatasetRow(BaseModel):
    kategori: KategoriDasar
    pesan: str
    kategori_nusaguard: KategoriNusaGuard

