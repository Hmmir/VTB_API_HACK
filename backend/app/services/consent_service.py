"""Business logic for consent management."""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.consent import (
    PartnerBank,
    ConsentRequest,
    Consent,
    ConsentEvent,
    ConsentStatus,
    ConsentScope,
)
from app.models.user import User


class ConsentService:
    """Service for managing user consents."""

    @staticmethod
    def get_or_create_partner_bank(db: Session, bank_code: str) -> PartnerBank:
        """Get existing partner bank or create a new one."""
        partner = db.query(PartnerBank).filter(PartnerBank.code == bank_code).first()
        
        if not partner:
            # Create new partner bank
            partner = PartnerBank(
                id=str(uuid4()),
                code=bank_code,
                name=f"{bank_code.upper()} Bank",
                api_endpoint=f"https://api.{bank_code}.com",
                jwks_uri=f"https://api.{bank_code}.com/.well-known/jwks.json"
            )
            db.add(partner)
            db.commit()
            db.refresh(partner)
        
        return partner

    @staticmethod
    def request_consent(
        db: Session,
        *,
        user_id: int,
        partner_bank_code: str,
        scopes: List[ConsentScope],
        purpose: Optional[str],
        valid_days: int = 90
    ) -> ConsentRequest:
        """Create a new consent request."""
        # Get or create partner bank
        partner_bank = ConsentService.get_or_create_partner_bank(db, partner_bank_code)
        
        # Check if there's already an active consent for the same scopes
        existing_consents = (
            db.query(Consent)
            .filter(
                Consent.user_id == user_id,
                Consent.partner_bank_id == partner_bank.id,
                Consent.status == ConsentStatus.ACTIVE,
                Consent.valid_until > datetime.utcnow()
            )
            .all()
        )
        
        for existing in existing_consents:
            if set(existing.scopes) == set([scope.value for scope in scopes]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Active consent with same scopes already exists"
                )
        
        # Create consent request
        valid_from = datetime.utcnow()
        valid_until = valid_from + timedelta(days=valid_days)
        
        consent_request = ConsentRequest(
            id=str(uuid4()),
            user_id=user_id,
            partner_bank_id=partner_bank.id,
            scopes=[scope.value for scope in scopes],
            purpose=purpose,
            status=ConsentStatus.REQUESTED,
            valid_from=valid_from,
            valid_until=valid_until
        )
        
        db.add(consent_request)
        db.commit()
        db.refresh(consent_request)
        
        return consent_request

    @staticmethod
    def approve_consent_request(
        db: Session,
        *,
        request_id: str,
        user_id: int
    ) -> Consent:
        """Approve a consent request and create active consent."""
        # Get consent request
        consent_request = (
            db.query(ConsentRequest)
            .filter(
                ConsentRequest.id == request_id,
                ConsentRequest.user_id == user_id,
                ConsentRequest.status == ConsentStatus.REQUESTED
            )
            .first()
        )
        
        if not consent_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consent request not found or already processed"
            )
        
        # Update request status
        consent_request.status = ConsentStatus.APPROVED
        consent_request.decided_at = datetime.utcnow()
        
        # Create active consent
        consent = Consent(
            id=str(uuid4()),
            request_id=consent_request.id,
            user_id=consent_request.user_id,
            partner_bank_id=consent_request.partner_bank_id,
            scopes=consent_request.scopes,
            status=ConsentStatus.ACTIVE,
            valid_from=consent_request.valid_from or datetime.utcnow(),
            valid_until=consent_request.valid_until or (datetime.utcnow() + timedelta(days=90))
        )
        
        db.add(consent)
        
        # Log event
        event = ConsentEvent(
            consent_id=consent.id,
            event_type="granted",
            description=f"Consent granted by user {user_id}",
            event_metadata={"scopes": consent.scopes}
        )
        db.add(event)
        
        db.commit()
        db.refresh(consent)
        
        return consent

    @staticmethod
    def reject_consent_request(
        db: Session,
        *,
        request_id: str,
        user_id: int,
        reason: Optional[str] = None
    ) -> ConsentRequest:
        """Reject a consent request."""
        consent_request = (
            db.query(ConsentRequest)
            .filter(
                ConsentRequest.id == request_id,
                ConsentRequest.user_id == user_id,
                ConsentRequest.status == ConsentStatus.REQUESTED
            )
            .first()
        )
        
        if not consent_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consent request not found or already processed"
            )
        
        consent_request.status = ConsentStatus.REJECTED
        consent_request.decided_at = datetime.utcnow()
        
        db.commit()
        db.refresh(consent_request)
        
        return consent_request

    @staticmethod
    def revoke_consent(
        db: Session,
        *,
        consent_id: str,
        user_id: int
    ) -> Consent:
        """Revoke an active consent."""
        consent = (
            db.query(Consent)
            .filter(
                Consent.id == consent_id,
                Consent.user_id == user_id,
                Consent.status == ConsentStatus.ACTIVE
            )
            .first()
        )
        
        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active consent not found"
            )
        
        consent.status = ConsentStatus.REVOKED
        consent.revoked_at = datetime.utcnow()
        
        # Log event
        event = ConsentEvent(
            consent_id=consent.id,
            event_type="revoked",
            description=f"Consent revoked by user {user_id}"
        )
        db.add(event)
        
        db.commit()
        db.refresh(consent)
        
        return consent

    @staticmethod
    def list_user_consents(
        db: Session,
        *,
        user_id: int,
        status: Optional[ConsentStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Consent], int]:
        """List user's consents with optional status filter."""
        query = db.query(Consent).filter(Consent.user_id == user_id)
        
        if status:
            query = query.filter(Consent.status == status)
        
        total = query.count()
        consents = query.order_by(Consent.granted_at.desc()).offset(offset).limit(limit).all()
        
        return consents, total

    @staticmethod
    def list_consent_requests(
        db: Session,
        *,
        user_id: int,
        status: Optional[ConsentStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[ConsentRequest], int]:
        """List user's consent requests."""
        query = db.query(ConsentRequest).filter(ConsentRequest.user_id == user_id)
        
        if status:
            query = query.filter(ConsentRequest.status == status)
        
        total = query.count()
        requests = query.order_by(ConsentRequest.requested_at.desc()).offset(offset).limit(limit).all()
        
        return requests, total

    @staticmethod
    def get_consent_events(
        db: Session,
        *,
        consent_id: str,
        user_id: int
    ) -> List[ConsentEvent]:
        """Get audit log for a consent."""
        # Verify user owns the consent
        consent = (
            db.query(Consent)
            .filter(
                Consent.id == consent_id,
                Consent.user_id == user_id
            )
            .first()
        )
        
        if not consent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consent not found"
            )
        
        return consent.events

    @staticmethod
    def verify_consent(
        db: Session,
        *,
        consent_id: str,
        partner_bank_code: str,
        required_scopes: List[ConsentScope]
    ) -> bool:
        """Verify if a consent is valid and has required scopes."""
        partner = db.query(PartnerBank).filter(PartnerBank.code == partner_bank_code).first()
        if not partner:
            return False
        
        consent = (
            db.query(Consent)
            .filter(
                Consent.id == consent_id,
                Consent.partner_bank_id == partner.id,
                Consent.status == ConsentStatus.ACTIVE,
                Consent.valid_until > datetime.utcnow()
            )
            .first()
        )
        
        if not consent:
            return False
        
        # Check if all required scopes are present
        consent_scopes = set(consent.scopes)
        required_scope_values = {scope.value for scope in required_scopes}
        
        return required_scope_values.issubset(consent_scopes)


__all__ = ["ConsentService"]

