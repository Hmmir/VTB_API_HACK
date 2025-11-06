"""Payments and Interbank Transfers API."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.payment import PaymentType, PaymentStatus, InterbankTransferStatus
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    InterbankTransferCreate,
    InterbankTransferResponse,
    InterbankTransferStatusUpdate,
    InternalTransferRequest,
    InternalTransferResponse,
)
from app.services.payment_service import PaymentService

router = APIRouter()


@router.post("/transfers/internal", response_model=InternalTransferResponse, status_code=status.HTTP_201_CREATED)
def create_internal_transfer(
    payload: InternalTransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Transfer funds between your own accounts.
    
    **Improved version** with proper payment lifecycle:
    - Creates Payment record
    - Updates account balances atomically
    - Creates transaction records for audit
    - Returns payment details
    
    **Replaces:** Old `/api/v1/accounts/transfer` endpoint
    """
    payment = PaymentService.process_internal_transfer(
        db,
        user_id=current_user.id,
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount=payload.amount,
        description=payload.description
    )
    
    return InternalTransferResponse(
        payment_id=payment.id,
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        status=payment.status,
        created_at=payment.created_at
    )


@router.post("/transfers/interbank", response_model=InterbankTransferResponse, status_code=status.HTTP_202_ACCEPTED)
def create_interbank_transfer(
    payload: InterbankTransferCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate interbank transfer (REQUIRES valid consent).
    
    **Use case:** Send money to another bank with consent validation.
    
    **Flow:**
    1. Validate active consent with PAYMENTS_WRITE scope
    2. Deduct from your account
    3. Create transfer record (status: INITIATED)
    4. Partner bank settles the transfer (webhook updates status)
    
    **Returns:** 202 Accepted (async processing)
    """
    transfer = PaymentService.initiate_interbank_transfer(
        db,
        user_id=current_user.id,
        from_account_id=payload.from_account_id,
        partner_bank_code=payload.partner_bank_code,
        counterparty_account=payload.counterparty_account,
        counterparty_name=payload.counterparty_name,
        amount=payload.amount,
        currency=payload.currency,
        purpose=payload.purpose,
        consent_id=payload.consent_id
    )
    
    return InterbankTransferResponse(
        id=transfer.id,
        user_id=transfer.user_id,
        from_account_id=transfer.from_account_id,
        partner_bank_id=transfer.partner_bank_id,
        partner_bank_code=transfer.partner_bank.code if transfer.partner_bank else None,
        counterparty_account=transfer.counterparty_account,
        counterparty_name=transfer.counterparty_name,
        amount=transfer.amount,
        currency=transfer.currency,
        purpose=transfer.purpose,
        consent_id=transfer.consent_id,
        status=transfer.status,
        transfer_metadata=transfer.transfer_metadata,
        initiated_at=transfer.initiated_at,
        settled_at=transfer.settled_at
    )


@router.get("/transfers/interbank", response_model=list[InterbankTransferResponse])
def list_interbank_transfers(
    status_filter: Optional[InterbankTransferStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List your interbank transfers.
    
    **Filters:**
    - status: initiated, pending_settlement, settled, failed
    """
    transfers, _ = PaymentService.list_interbank_transfers(
        db,
        user_id=current_user.id,
        status=status_filter,
        limit=limit,
        offset=offset
    )
    
    return [
        InterbankTransferResponse(
            id=t.id,
            user_id=t.user_id,
            from_account_id=t.from_account_id,
            partner_bank_id=t.partner_bank_id,
            partner_bank_code=t.partner_bank.code if t.partner_bank else None,
            counterparty_account=t.counterparty_account,
            counterparty_name=t.counterparty_name,
            amount=t.amount,
            currency=t.currency,
            purpose=t.purpose,
            consent_id=t.consent_id,
            status=t.status,
            transfer_metadata=t.transfer_metadata,
            initiated_at=t.initiated_at,
            settled_at=t.settled_at
        )
        for t in transfers
    ]


@router.post("/transfers/interbank/{transfer_id}/status", response_model=InterbankTransferResponse)
def update_interbank_transfer_status(
    transfer_id: str,
    payload: InterbankTransferStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update interbank transfer status (webhook/admin endpoint).
    
    **Use case:** Partner bank notifies us about settlement.
    
    **Production:** Secure this endpoint with RS256 JWT validation.
    """
    transfer = PaymentService.update_interbank_status(
        db,
        transfer_id=transfer_id,
        new_status=payload.status,
        settled_at=payload.settled_at,
        metadata=payload.metadata
    )
    
    return InterbankTransferResponse(
        id=transfer.id,
        user_id=transfer.user_id,
        from_account_id=transfer.from_account_id,
        partner_bank_id=transfer.partner_bank_id,
        partner_bank_code=transfer.partner_bank.code if transfer.partner_bank else None,
        counterparty_account=transfer.counterparty_account,
        counterparty_name=transfer.counterparty_name,
        amount=transfer.amount,
        currency=transfer.currency,
        purpose=transfer.purpose,
        consent_id=transfer.consent_id,
        status=transfer.status,
        transfer_metadata=transfer.transfer_metadata,
        initiated_at=transfer.initiated_at,
        settled_at=transfer.settled_at
    )


@router.get("/payments", response_model=list[PaymentResponse])
def list_payments(
    payment_type: Optional[PaymentType] = Query(None, alias="type"),
    status_filter: Optional[PaymentStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all your payments (internal, interbank, partner).
    
    **Filters:**
    - type: internal, interbank, partner
    - status: created, processing, completed, failed, cancelled
    """
    payments, _ = PaymentService.list_user_payments(
        db,
        user_id=current_user.id,
        payment_type=payment_type,
        status=status_filter,
        limit=limit,
        offset=offset
    )
    
    return [
        PaymentResponse(
            id=p.id,
            user_id=p.user_id,
            account_id=p.account_id,
            amount=p.amount,
            currency=p.currency,
            counterparty=p.counterparty,
            description=p.description,
            payment_type=p.payment_type,
            status=p.status,
            consent_id=p.consent_id,
            payment_metadata=p.payment_metadata,
            created_at=p.created_at,
            completed_at=p.completed_at
        )
        for p in payments
    ]


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment details by ID.
    
    **Use case:** Track payment status for UI updates.
    """
    from app.models.payment import Payment
    
    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.user_id == current_user.id
        )
        .first()
    )
    
    if not payment:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return PaymentResponse(
        id=payment.id,
        user_id=payment.user_id,
        account_id=payment.account_id,
        amount=payment.amount,
        currency=payment.currency,
        counterparty=payment.counterparty,
        description=payment.description,
        payment_type=payment.payment_type,
        status=payment.status,
        consent_id=payment.consent_id,
        payment_metadata=payment.payment_metadata,
        created_at=payment.created_at,
        completed_at=payment.completed_at
    )

