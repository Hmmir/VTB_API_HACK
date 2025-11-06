"""Business logic for product agreements (deposits, credits, cards)."""
from __future__ import annotations
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import List, Optional
from uuid import uuid4
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.bank_product import BankProduct
from app.models.product_agreement import (
    ProductAgreement,
    ProductType,
    AgreementStatus,
    PaymentScheduleType,
    PaymentSchedule,
    AgreementEvent,
)
from app.models.account import Account
from app.models.user import User


class ProductAgreementService:
    """Service for managing product agreements."""

    @staticmethod
    def _generate_agreement_number() -> str:
        """Generate unique agreement number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid4())[:8].upper()
        return f"AGR-{timestamp}-{random_suffix}"

    @staticmethod
    def _calculate_annuity_payment(principal: Decimal, annual_rate: Decimal, months: int) -> Decimal:
        """Calculate monthly annuity payment."""
        if annual_rate == 0:
            return principal / months
        
        monthly_rate = annual_rate / Decimal("1200")  # Convert annual % to monthly decimal
        payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
        return payment.quantize(Decimal("0.01"))

    @staticmethod
    def _generate_payment_schedule(
        agreement: ProductAgreement,
        schedule_type: PaymentScheduleType
    ) -> List[PaymentSchedule]:
        """Generate payment schedule for credit/loan."""
        schedules = []
        remaining_principal = agreement.amount
        
        if schedule_type == PaymentScheduleType.ANNUITY:
            monthly_payment = ProductAgreementService._calculate_annuity_payment(
                agreement.amount,
                agreement.interest_rate,
                agreement.term_months
            )
            
            for i in range(1, agreement.term_months + 1):
                due_date = agreement.start_date + relativedelta(months=i)
                monthly_rate = agreement.interest_rate / Decimal("1200")
                
                interest = (remaining_principal * monthly_rate).quantize(Decimal("0.01"))
                principal = (monthly_payment - interest).quantize(Decimal("0.01"))
                
                # Last payment adjustment
                if i == agreement.term_months:
                    principal = remaining_principal
                    total = principal + interest
                else:
                    total = monthly_payment
                
                schedule = PaymentSchedule(
                    id=str(uuid4()),
                    agreement_id=agreement.id,
                    payment_number=i,
                    due_date=due_date,
                    principal_amount=principal,
                    interest_amount=interest,
                    total_amount=total
                )
                schedules.append(schedule)
                remaining_principal -= principal
        
        elif schedule_type == PaymentScheduleType.DIFFERENTIATED:
            principal_payment = (agreement.amount / agreement.term_months).quantize(Decimal("0.01"))
            
            for i in range(1, agreement.term_months + 1):
                due_date = agreement.start_date + relativedelta(months=i)
                monthly_rate = agreement.interest_rate / Decimal("1200")
                
                interest = (remaining_principal * monthly_rate).quantize(Decimal("0.01"))
                principal = principal_payment if i < agreement.term_months else remaining_principal
                total = principal + interest
                
                schedule = PaymentSchedule(
                    id=str(uuid4()),
                    agreement_id=agreement.id,
                    payment_number=i,
                    due_date=due_date,
                    principal_amount=principal,
                    interest_amount=interest,
                    total_amount=total
                )
                schedules.append(schedule)
                remaining_principal -= principal
        
        return schedules

    @staticmethod
    def create_agreement(
        db: Session,
        *,
        user_id: int,
        bank_product_id: str,  # Changed to str - external product ID
        amount: Decimal,
        term_months: int,
        linked_account_id: Optional[int],
        payment_schedule_type: Optional[PaymentScheduleType],
        credit_limit: Optional[Decimal]
    ) -> ProductAgreement:
        """Create new product agreement (draft status)."""
        # Note: bank_product_id is a string reference to external bank API product
        # We don't validate it against local DB since products come from external APIs
        
        # Validate linked account if provided
        if linked_account_id:
            account = (
                db.query(Account)
                .join(Account.bank_connection)
                .filter(
                    Account.id == linked_account_id,
                    Account.bank_connection.has(user_id=user_id)
                )
                .first()
            )
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Linked account not found"
                )
        
        # Determine product type from bank_product_id string
        # Format: "prod-{bank}-{type}-{id}"
        product_type = ProductType.DEPOSIT
        product_id_lower = bank_product_id.lower()
        
        if "credit" in product_id_lower or "loan" in product_id_lower:
            product_type = ProductType.CREDIT
        elif "card" in product_id_lower:
            product_type = ProductType.CARD
        elif "mortgage" in product_id_lower:
            product_type = ProductType.MORTGAGE
        
        # Default interest rate (will be updated from product data if available)
        interest_rate = Decimal("10.0")
        
        # Create agreement
        start_date = datetime.utcnow().date()
        end_date = start_date + relativedelta(months=term_months)
        
        agreement = ProductAgreement(
            id=str(uuid4()),
            user_id=user_id,
            bank_product_id=bank_product_id,
            agreement_number=ProductAgreementService._generate_agreement_number(),
            product_type=product_type,
            status=AgreementStatus.DRAFT,
            amount=amount,
            interest_rate=interest_rate,
            term_months=term_months,
            start_date=start_date,
            end_date=end_date,
            linked_account_id=linked_account_id,
            payment_schedule_type=payment_schedule_type,
            credit_limit=credit_limit,
            available_limit=credit_limit,
            outstanding_balance=amount if product_type in [ProductType.CREDIT, ProductType.LOAN, ProductType.MORTGAGE] else None
        )
        
        # Calculate monthly payment for credits
        if product_type in [ProductType.CREDIT, ProductType.LOAN, ProductType.MORTGAGE] and payment_schedule_type:
            agreement.monthly_payment = ProductAgreementService._calculate_annuity_payment(
                amount,
                agreement.interest_rate,
                term_months
            )
        
        db.add(agreement)
        
        # Log event
        event = AgreementEvent(
            agreement_id=agreement.id,
            event_type="created",
            description=f"Agreement created for product {bank_product_id}"
        )
        db.add(event)
        
        db.commit()
        db.refresh(agreement)
        
        return agreement

    @staticmethod
    def sign_agreement(
        db: Session,
        *,
        agreement_id: str,
        user_id: int,
        signature: str
    ) -> ProductAgreement:
        """Sign agreement to activate it."""
        agreement = (
            db.query(ProductAgreement)
            .filter(
                ProductAgreement.id == agreement_id,
                ProductAgreement.user_id == user_id,
                ProductAgreement.status == AgreementStatus.DRAFT
            )
            .first()
        )
        
        if not agreement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft agreement not found"
            )
        
        # Activate agreement
        agreement.status = AgreementStatus.ACTIVE
        agreement.signed_at = datetime.utcnow()
        
        # Generate payment schedule for credits
        if agreement.product_type in [ProductType.CREDIT, ProductType.LOAN, ProductType.MORTGAGE]:
            if agreement.payment_schedule_type:
                schedules = ProductAgreementService._generate_payment_schedule(
                    agreement,
                    agreement.payment_schedule_type
                )
                for schedule in schedules:
                    db.add(schedule)
        
        # Log event
        event = AgreementEvent(
            agreement_id=agreement.id,
            event_type="signed",
            description="Agreement signed and activated",
            event_metadata={"signature_hash": signature[:20]}
        )
        db.add(event)
        
        db.commit()
        db.refresh(agreement)
        
        return agreement

    @staticmethod
    def list_user_agreements(
        db: Session,
        *,
        user_id: int,
        product_type: Optional[ProductType] = None,
        status: Optional[AgreementStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[ProductAgreement], int]:
        """List user's agreements with filters."""
        query = db.query(ProductAgreement).filter(ProductAgreement.user_id == user_id)
        
        if product_type:
            query = query.filter(ProductAgreement.product_type == product_type)
        if status:
            query = query.filter(ProductAgreement.status == status)
        
        total = query.count()
        agreements = query.order_by(ProductAgreement.created_at.desc()).offset(offset).limit(limit).all()
        
        return agreements, total

    @staticmethod
    def get_agreement_with_schedule(
        db: Session,
        *,
        agreement_id: str,
        user_id: int
    ) -> ProductAgreement:
        """Get agreement with payment schedule."""
        agreement = (
            db.query(ProductAgreement)
            .filter(
                ProductAgreement.id == agreement_id,
                ProductAgreement.user_id == user_id
            )
            .first()
        )
        
        if not agreement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agreement not found"
            )
        
        return agreement

    @staticmethod
    def close_agreement(
        db: Session,
        *,
        agreement_id: str,
        user_id: int,
        reason: Optional[str]
    ) -> ProductAgreement:
        """Close agreement early."""
        agreement = (
            db.query(ProductAgreement)
            .filter(
                ProductAgreement.id == agreement_id,
                ProductAgreement.user_id == user_id,
                ProductAgreement.status == AgreementStatus.ACTIVE
            )
            .first()
        )
        
        if not agreement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active agreement not found"
            )
        
        # Check if credit is fully paid
        if agreement.product_type in [ProductType.CREDIT, ProductType.LOAN, ProductType.MORTGAGE]:
            if agreement.outstanding_balance and agreement.outstanding_balance > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot close: outstanding balance {agreement.outstanding_balance}"
                )
        
        agreement.status = AgreementStatus.CLOSED
        agreement.closed_at = datetime.utcnow()
        
        # Log event
        event = AgreementEvent(
            agreement_id=agreement.id,
            event_type="closed",
            description=reason or "Agreement closed by user"
        )
        db.add(event)
        
        db.commit()
        db.refresh(agreement)
        
        return agreement


__all__ = ["ProductAgreementService"]

