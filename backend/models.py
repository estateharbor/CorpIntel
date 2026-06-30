"""Pydantic request/response models for CorpIntel India."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------- Auth ----------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MagicLinkRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"


class UserPublic(BaseModel):
    user_id: str
    email: str
    name: str
    plan: str = "free"
    picture: Optional[str] = None
    searches_used: int = 0
    exports_used: int = 0
    api_key: Optional[str] = None
    auth_provider: str = "email"
    created_at: Optional[datetime] = None


# ---------------- Companies / LLPs (entities) ----------------
class Director(BaseModel):
    din: str
    name: str
    cin: str
    designation: str
    date_of_appointment: Optional[datetime] = None
    is_active: bool = True


class Partner(BaseModel):
    """LLP designated partner (parallel to Director for Companies)."""
    dpin: str
    name: str
    llpin: str
    designation: str = "Designated Partner"
    date_of_appointment: Optional[datetime] = None
    is_active: bool = True


class CompanySummary(BaseModel):
    cin: Optional[str] = None
    # Generic entity identity (Company -> CIN, LLP -> LLPIN)
    identifier: Optional[str] = None
    identifier_type: Optional[str] = None  # "CIN" | "LLPIN"
    entity_type: str = "Company"           # "Company" | "LLP"
    name: str
    status: str
    company_class: Optional[str] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None
    date_of_incorporation: Optional[datetime] = None
    paid_up_capital: float = 0
    authorized_capital: float = 0
    total_contribution: Optional[float] = None  # LLP-specific
    director_count: int = 0
    data_quality_score: int = 0
    enriched: bool = False


class CompanyDetail(CompanySummary):
    llpin: Optional[str] = None
    category: Optional[str] = None
    principal_activity: Optional[str] = None
    b2b_or_b2c: Optional[str] = None
    roc: Optional[str] = None
    address: Optional[str] = None
    pin_code: Optional[str] = None
    registered_state: Optional[str] = None
    data_source: Optional[str] = None
    interesting_flag: Optional[bool] = None
    interesting_reason: Optional[str] = None


# ---------------- CSV upload ----------------
class RejectedRow(BaseModel):
    row_number: int
    identifier: Optional[str] = None
    reason: str


class UploadSummary(BaseModel):
    ok: bool = True
    total_rows: int = 0
    processed: int = 0
    companies_inserted: int = 0
    companies_updated: int = 0
    llps_inserted: int = 0
    llps_updated: int = 0
    rejected_count: int = 0
    rejected_rows: List[RejectedRow] = Field(default_factory=list)
    message: Optional[str] = None


class PaginatedCompanies(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    results: List[CompanySummary]


class ContactInfo(BaseModel):
    cin: str
    gstin: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    locked: bool = False
    message: Optional[str] = None


# ---------------- Search ----------------
class AdvancedSearchRequest(BaseModel):
    search: Optional[str] = None
    city: Optional[List[str]] = None
    sector: Optional[List[str]] = None
    status: Optional[str] = None
    company_class: Optional[str] = None
    entity_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    min_capital: Optional[float] = None
    max_capital: Optional[float] = None
    sort_by: str = "date_of_incorporation"
    order: str = "desc"
    page: int = 1
    limit: int = 50


class SaveSearchRequest(BaseModel):
    name: str
    criteria: Dict[str, Any]


# ---------------- Alerts ----------------
class AlertRequest(BaseModel):
    name: str
    cities: List[str] = Field(default_factory=list)
    sectors: List[str] = Field(default_factory=list)
    min_capital: Optional[float] = None
    frequency: str = "weekly"  # daily | weekly


class Alert(AlertRequest):
    id: str
    last_triggered: Optional[datetime] = None
    active: bool = True
    match_count: int = 0


# ---------------- Export ----------------
class ExportRequest(BaseModel):
    search: Optional[str] = None
    city: Optional[List[str]] = None
    sector: Optional[List[str]] = None
    status: Optional[str] = None
    company_class: Optional[str] = None
    entity_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    min_capital: Optional[float] = None
    max_capital: Optional[float] = None
    limit: int = 5000


# ---------------- Payments ----------------
class CheckoutRequest(BaseModel):
    plan_id: str  # starter | pro
    origin_url: str


class CheckoutResponse(BaseModel):
    url: str
    session_id: str


TokenResponse.model_rebuild()
