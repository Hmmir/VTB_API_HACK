"""Pydantic schemas for consent management."""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.consent import ConsentStatus, ConsentScope


class ConsentRequestCreate(BaseModel):
    """Request to create a new consent request."""
    partner_bank_code: str = Field(..., description="Partner bank identifier")
    scopes: List[ConsentScope] = Field(..., description="Requested permissions")
    purpose: Optional[str] = Field(None, description="Purpose of data access")
    valid_days: int = Field(90, ge=1, le=365, description="Validity period in days")


class ConsentRequestResponse(BaseModel):
    """Consent request details."""
    id: str
    user_id: int
    partner_bank_id: str
    partner_bank_name: str
    scopes: List[str]
    purpose: Optional[str]
    status: ConsentStatus
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    requested_at: datetime
    decided_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConsentDecisionRequest(BaseModel):
    """User decision on consent request (approve/reject)."""
    decision: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = None


class ConsentResponse(BaseModel):
    """Active consent details."""
    id: str
    request_id: str
    user_id: int
    partner_bank_id: str
    partner_bank_name: str
    scopes: List[str]
    status: ConsentStatus
    valid_from: datetime
    valid_until: datetime
    granted_at: datetime
    revoked_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConsentEventResponse(BaseModel):
    """Consent audit event."""
    id: int
    consent_id: str
    event_type: str
    description: Optional[str]
    event_metadata: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class ConsentListResponse(BaseModel):
    """List of consents with pagination."""
    consents: List[ConsentResponse]
    total: int
    page: int
    page_size: int


class PartnerBankResponse(BaseModel):
    """Partner bank information."""
    id: str
    code: str
    name: str
    api_endpoint: Optional[str]
    jwks_uri: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


__all__ = [
    "ConsentRequestCreate",
    "ConsentRequestResponse",
    "ConsentDecisionRequest",
    "ConsentResponse",
    "ConsentEventResponse",
    "ConsentListResponse",
    "PartnerBankResponse",
]

