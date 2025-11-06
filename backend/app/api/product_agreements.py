"""Product Agreements API (deposits, credits, cards)."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.product_agreement import ProductType, AgreementStatus
from app.schemas.product_agreement import (
    ProductAgreementCreate,
    ProductAgreementSign,
    ProductAgreementResponse,
    ProductAgreementWithSchedule,
    PaymentScheduleResponse,
    AgreementListResponse,
    AgreementCloseRequest,
)
from app.services.product_agreement_service import ProductAgreementService

router = APIRouter()


@router.post("/agreements", response_model=ProductAgreementResponse, status_code=status.HTTP_201_CREATED)
def create_product_agreement(
    payload: ProductAgreementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new product agreement (DRAFT status).
    
    **Use case:** User applies for credit/deposit/card.
    
    **Flow:**
    1. Select bank product (from /api/v1/products)
    2. Submit application with amount and term
    3. Agreement created in DRAFT status
    4. User reviews terms and signs (POST /agreements/{id}/sign)
    
    **Product types:**
    - Deposit: User deposits money, earns interest
    - Credit/Loan: User borrows money, pays with schedule
    - Card: Credit card with limit
    - Mortgage: Long-term loan for real estate
    """
    agreement = ProductAgreementService.create_agreement(
        db,
        user_id=current_user.id,
        bank_product_id=payload.bank_product_id,
        amount=payload.amount,
        term_months=payload.term_months,
        linked_account_id=payload.linked_account_id,
        payment_schedule_type=payload.payment_schedule_type,
        credit_limit=payload.credit_limit
    )
    
    return ProductAgreementResponse.from_orm(agreement)


@router.post("/agreements/{agreement_id}/sign", response_model=ProductAgreementResponse)
def sign_product_agreement(
    agreement_id: str,
    payload: ProductAgreementSign,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sign agreement to activate it.
    
    **Use case:** User accepts terms and activates agreement.
    
    **Flow:**
    1. Agreement status: DRAFT → ACTIVE
    2. For credits: Payment schedule generated
    3. For deposits: Interest accrual starts
    4. For cards: Card number assigned (masked)
    
    **Signature:** Digital signature or PIN (demo accepts any string).
    """
    agreement = ProductAgreementService.sign_agreement(
        db,
        agreement_id=agreement_id,
        user_id=current_user.id,
        signature=payload.signature
    )
    
    return ProductAgreementResponse.from_orm(agreement)


@router.get("/agreements", response_model=AgreementListResponse)
def list_product_agreements(
    product_type: Optional[ProductType] = Query(None, alias="type"),
    status_filter: Optional[AgreementStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List your product agreements.
    
    **Filters:**
    - type: deposit, credit, card, loan, mortgage
    - status: draft, active, suspended, closed, cancelled
    """
    agreements, total = ProductAgreementService.list_user_agreements(
        db,
        user_id=current_user.id,
        product_type=product_type,
        status=status_filter,
        limit=limit,
        offset=offset
    )
    
    return AgreementListResponse(
        agreements=[ProductAgreementResponse.from_orm(a) for a in agreements],
        total=total
    )


@router.get("/agreements/{agreement_id}", response_model=ProductAgreementWithSchedule)
def get_product_agreement(
    agreement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get agreement details with payment schedule.
    
    **Use case:** View full agreement terms and payment plan.
    
    **Returns:**
    - Agreement details
    - Payment schedule (for credits/loans)
    - Payment history
    """
    agreement = ProductAgreementService.get_agreement_with_schedule(
        db,
        agreement_id=agreement_id,
        user_id=current_user.id
    )
    
    response = ProductAgreementWithSchedule.from_orm(agreement)
    response.payment_schedules = [
        PaymentScheduleResponse.from_orm(s) for s in agreement.payment_schedules
    ]
    
    return response


@router.post("/agreements/{agreement_id}/close", response_model=ProductAgreementResponse)
def close_product_agreement(
    agreement_id: str,
    payload: AgreementCloseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Close agreement early.
    
    **Use case:** User closes deposit or pays off credit early.
    
    **Requirements:**
    - Agreement must be ACTIVE
    - For credits: Outstanding balance must be 0
    
    **Status:** ACTIVE → CLOSED
    """
    agreement = ProductAgreementService.close_agreement(
        db,
        agreement_id=agreement_id,
        user_id=current_user.id,
        reason=payload.reason
    )
    
    return ProductAgreementResponse.from_orm(agreement)


@router.get("/agreements/{agreement_id}/schedule", response_model=list[PaymentScheduleResponse])
def get_payment_schedule(
    agreement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment schedule for credit/loan.
    
    **Use case:** View detailed payment plan.
    
    **Returns:** List of scheduled payments with:
    - Payment number
    - Due date
    - Principal amount
    - Interest amount
    - Total amount
    - Payment status (paid/unpaid/overdue)
    """
    agreement = ProductAgreementService.get_agreement_with_schedule(
        db,
        agreement_id=agreement_id,
        user_id=current_user.id
    )
    
    return [PaymentScheduleResponse.from_orm(s) for s in agreement.payment_schedules]

