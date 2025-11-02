"""Consent Management API endpoints (OpenBanking Russia v2.1 compatible)."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.consent import ConsentStatus
from app.schemas.consent import (
    ConsentRequestCreate,
    ConsentRequestResponse,
    ConsentDecisionRequest,
    ConsentResponse,
    ConsentEventResponse,
    ConsentListResponse,
)
from app.services.consent_service import ConsentService

router = APIRouter()


@router.post("/request", response_model=ConsentRequestResponse, status_code=status.HTTP_201_CREATED)
def request_consent(
    payload: ConsentRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request user consent for data access (OpenBanking).
    
    **Scenario:** Partner bank (e.g., VBank) wants to access FinanceHub user's data.
    
    **Flow:**
    1. Partner bank calls this endpoint with required scopes
    2. User receives notification about consent request
    3. User approves/rejects via UI or `/requests/{id}/approve` endpoint
    """
    consent_request = ConsentService.request_consent(
        db,
        user_id=current_user.id,
        partner_bank_code=payload.partner_bank_code,
        scopes=payload.scopes,
        purpose=payload.purpose,
        valid_days=payload.valid_days
    )
    
    return ConsentRequestResponse(
        id=consent_request.id,
        user_id=consent_request.user_id,
        partner_bank_id=consent_request.partner_bank_id,
        partner_bank_name=consent_request.partner_bank.name,
        scopes=consent_request.scopes,
        purpose=consent_request.purpose,
        status=consent_request.status,
        valid_from=consent_request.valid_from,
        valid_until=consent_request.valid_until,
        requested_at=consent_request.requested_at,
        decided_at=consent_request.decided_at
    )


@router.get("/requests", response_model=list[ConsentRequestResponse])
def list_consent_requests(
    status_filter: Optional[ConsentStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's consent requests.
    
    **Use cases:**
    - View all pending consent requests
    - Review consent request history
    - Filter by status (requested, approved, rejected)
    """
    requests, _ = ConsentService.list_consent_requests(
        db,
        user_id=current_user.id,
        status=status_filter,
        limit=limit,
        offset=offset
    )
    
    return [
        ConsentRequestResponse(
            id=req.id,
            user_id=req.user_id,
            partner_bank_id=req.partner_bank_id,
            partner_bank_name=req.partner_bank.name,
            scopes=req.scopes,
            purpose=req.purpose,
            status=req.status,
            valid_from=req.valid_from,
            valid_until=req.valid_until,
            requested_at=req.requested_at,
            decided_at=req.decided_at
        )
        for req in requests
    ]


@router.post("/requests/{request_id}/approve", response_model=ConsentResponse)
def approve_consent_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a consent request.
    
    **Result:** Creates an active consent that partner bank can use for API calls.
    """
    consent = ConsentService.approve_consent_request(
        db,
        request_id=request_id,
        user_id=current_user.id
    )
    
    return ConsentResponse(
        id=consent.id,
        request_id=consent.request_id,
        user_id=consent.user_id,
        partner_bank_id=consent.partner_bank_id,
        partner_bank_name=consent.partner_bank.name,
        scopes=consent.scopes,
        status=consent.status,
        valid_from=consent.valid_from,
        valid_until=consent.valid_until,
        granted_at=consent.granted_at,
        revoked_at=consent.revoked_at
    )


@router.post("/requests/{request_id}/reject", response_model=ConsentRequestResponse)
def reject_consent_request(
    request_id: str,
    payload: ConsentDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a consent request.
    
    **Result:** Consent request is marked as rejected, partner bank cannot access data.
    """
    consent_request = ConsentService.reject_consent_request(
        db,
        request_id=request_id,
        user_id=current_user.id,
        reason=payload.reason
    )
    
    return ConsentRequestResponse(
        id=consent_request.id,
        user_id=consent_request.user_id,
        partner_bank_id=consent_request.partner_bank_id,
        partner_bank_name=consent_request.partner_bank.name,
        scopes=consent_request.scopes,
        purpose=consent_request.purpose,
        status=consent_request.status,
        valid_from=consent_request.valid_from,
        valid_until=consent_request.valid_until,
        requested_at=consent_request.requested_at,
        decided_at=consent_request.decided_at
    )


@router.get("/my-consents", response_model=ConsentListResponse)
def list_my_consents(
    status_filter: Optional[ConsentStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's active and historical consents.
    
    **Use cases:**
    - View all active consents
    - Review consent history
    - See which banks have access to your data
    """
    offset = (page - 1) * page_size
    
    consents, total = ConsentService.list_user_consents(
        db,
        user_id=current_user.id,
        status=status_filter,
        limit=page_size,
        offset=offset
    )
    
    consent_responses = [
        ConsentResponse(
            id=consent.id,
            request_id=consent.request_id,
            user_id=consent.user_id,
            partner_bank_id=consent.partner_bank_id,
            partner_bank_name=consent.partner_bank.name,
            scopes=consent.scopes,
            status=consent.status,
            valid_from=consent.valid_from,
            valid_until=consent.valid_until,
            granted_at=consent.granted_at,
            revoked_at=consent.revoked_at
        )
        for consent in consents
    ]
    
    return ConsentListResponse(
        consents=consent_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{consent_id}", status_code=status.HTTP_200_OK)
def revoke_consent(
    consent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke (delete) an active consent.
    
    **Result:** Partner bank immediately loses access to your data.
    
    **Compliance:** Required by OpenBanking Russia v2.1 and GDPR.
    """
    consent = ConsentService.revoke_consent(
        db,
        consent_id=consent_id,
        user_id=current_user.id
    )
    
    return {
        "message": "Consent revoked successfully",
        "consent_id": consent.id,
        "revoked_at": consent.revoked_at
    }


@router.get("/{consent_id}/events", response_model=list[ConsentEventResponse])
def get_consent_events(
    consent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit log for a consent.
    
    **Returns:** All events related to the consent (granted, accessed, revoked, etc.)
    
    **Compliance:** Required for security audits and user transparency.
    """
    events = ConsentService.get_consent_events(
        db,
        consent_id=consent_id,
        user_id=current_user.id
    )
    
    return [
        ConsentEventResponse(
            id=event.id,
            consent_id=event.consent_id,
            event_type=event.event_type,
            description=event.description,
            event_metadata=event.event_metadata,
            created_at=event.created_at
        )
        for event in events
    ]

