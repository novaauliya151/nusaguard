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
    source: str | None = Field(default="public_form", max_length=50)
    additional_notes: str | None = Field(default=None, max_length=1000)

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
    status: Literal["pending", "reviewed", "in_review", "approved", "rejected", "needs_anonymization", "dataset_candidate"]
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
    analyses_today: int
    analyses_this_month: int
    reports_reviewed: int
    candidates_total: int
    education_published: int

class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    role: str
    permissions: list[str]
    is_active: bool
    status: str = "active"
    avatar: str | None = None
    must_change_password: bool = False
    last_login_at: datetime | None = None
    created_by: str | None = None
    updated_at: datetime | None = None
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
    role: str = Field(default="user", min_length=2, max_length=40)
    status: Literal["active", "suspended", "inactive"] = "active"
    must_change_password: bool = True
    confirm_password: str | None = None

class UserUpdateRequest(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)] | None = None
    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=160, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")] | None = None
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)] | None = None
    role: str | None = Field(default=None, min_length=2, max_length=40)
    is_active: bool | None = None
    status: Literal["active", "suspended", "inactive"] | None = None
    avatar: str | None = Field(default=None, max_length=500)
    must_change_password: bool | None = None
    suspension_reason: str | None = Field(default=None, max_length=500)

class PasswordResetRequest(BaseModel):
    password: Annotated[str, StringConstraints(min_length=10, max_length=128)]
    confirm_password: Annotated[str, StringConstraints(min_length=10, max_length=128)]
    must_change_password: bool = True

class RoleRequest(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
    slug: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=40)]
    description: str | None = Field(default=None, max_length=500)
    permissions: list[str] = Field(default_factory=list, max_length=100)

class EducationItemRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=120)]
    category: KategoriNusaGuard
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=1000)]
    warning_signs: list[str] = Field(min_length=1, max_length=10)
    prevention: list[str] = Field(min_length=1, max_length=10)
    is_published: bool = True
    slug: str | None = Field(default=None, max_length=160)
    summary: str | None = Field(default=None, max_length=500)
    content: str | None = Field(default=None, max_length=20000)
    anonymized_example: str | None = Field(default=None, max_length=5000)
    response_steps: list[str] = Field(default_factory=list, max_length=20)
    thumbnail: str | None = Field(default=None, max_length=500)
    image_alt: str | None = Field(default=None, max_length=240)
    meta_title: str | None = Field(default=None, max_length=160)
    meta_description: str | None = Field(default=None, max_length=500)
    status: Literal["draft", "scheduled", "published", "archived"] = "published"
    published_at: datetime | None = None
    display_order: int = Field(default=0, ge=0, le=10000)

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

class ReportValidationRequest(BaseModel):
    status: Literal["pending", "in_review", "approved", "rejected", "needs_anonymization", "dataset_candidate"] | None = None
    correct_category: KategoriNusaGuard | None = None
    validation_notes: str | None = Field(default=None, max_length=2000)
    is_duplicate: bool | None = None
    admin_result: str | None = Field(default=None, max_length=2000)

class DatasetCandidateRequest(BaseModel):
    report_id: str | None = None
    text_anonymized: MessageText
    category: KategoriNusaGuard
    source: str = "manual_admin"
    data_type: Literal["primer", "sekunder", "sintetis"] = "primer"
    validation_status: Literal["pending", "approved", "rejected", "verified"] = "pending"
    split: Literal["train", "validation", "test"] | None = None
    validator: str | None = None
    notes: str | None = None
    is_duplicate: bool = False
    is_archived: bool = False
    nseae_validation: dict[str, bool] = Field(default_factory=dict)

class DatasetCandidate(DatasetCandidateRequest):
    id: str
    created_at: datetime
    updated_at: datetime

class PasswordChangeRequest(BaseModel):
    current_password: Annotated[str, StringConstraints(min_length=8, max_length=128)]
    new_password: Annotated[str, StringConstraints(min_length=8, max_length=128)]

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

