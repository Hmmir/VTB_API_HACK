"""Bank Capital API - Капитал банков с улучшенной обработкой ошибок"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
import logging

from ..database import get_db
from ..models import BankCapital, User
from .dependencies import get_current_user

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bank-capital", tags=["Bank Capital"])


# ============================================================================
# Pydantic Schemas with Validation
# ============================================================================

class BankCapitalResponse(BaseModel):
    id: int
    bank_code: str
    bank_name: str
    total_capital: float
    tier1_capital: float
    tier2_capital: float
    total_assets: float
    total_liabilities: float
    capital_adequacy_ratio: Optional[float]
    liquidity_ratio: Optional[float]
    max_loan_amount: Optional[float]
    interbank_limit: Optional[float]
    is_active: bool
    is_partner: bool
    last_audit_date: Optional[datetime]
    capital_adequacy_percentage: float
    leverage_ratio: float
    
    class Config:
        from_attributes = True


class BankCapitalCreate(BaseModel):
    bank_code: str = Field(..., min_length=2, max_length=50, description="Код банка")
    bank_name: str = Field(..., min_length=3, max_length=255, description="Название банка")
    total_capital: Decimal = Field(default=Decimal("0.00"), ge=0, description="Общий капитал")
    tier1_capital: Decimal = Field(default=Decimal("0.00"), ge=0, description="Капитал 1 уровня")
    tier2_capital: Decimal = Field(default=Decimal("0.00"), ge=0, description="Капитал 2 уровня")
    total_assets: Decimal = Field(default=Decimal("0.00"), ge=0, description="Всего активов")
    total_liabilities: Decimal = Field(default=Decimal("0.00"), ge=0, description="Всего обязательств")
    
    @validator('tier1_capital', 'tier2_capital')
    def validate_capital_components(cls, v, values):
        """Проверить что компоненты капитала не превышают общий капитал"""
        if 'total_capital' in values and v > values['total_capital']:
            raise ValueError('Компонент капитала не может превышать общий капитал')
        return v


class BankCapitalUpdate(BaseModel):
    total_capital: Optional[Decimal] = Field(None, ge=0)
    tier1_capital: Optional[Decimal] = Field(None, ge=0)
    tier2_capital: Optional[Decimal] = Field(None, ge=0)
    total_assets: Optional[Decimal] = Field(None, ge=0)
    total_liabilities: Optional[Decimal] = Field(None, ge=0)
    capital_adequacy_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    liquidity_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    max_loan_amount: Optional[Decimal] = Field(None, ge=0)
    interbank_limit: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_partner: Optional[bool] = None
    last_audit_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)


# ============================================================================
# Helper Functions
# ============================================================================

def handle_database_error(error: Exception, operation: str):
    """Централизованная обработка ошибок БД"""
    logger.error(f"Database error during {operation}: {str(error)}", exc_info=True)
    
    if isinstance(error, IntegrityError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Конфликт данных: возможно, банк с таким кодом уже существует"
        )
    elif isinstance(error, SQLAlchemyError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при выполнении операции: {operation}"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при выполнении: {operation}"
        )


# ============================================================================
# API Endpoints with Improved Error Handling
# ============================================================================

@router.get("/", response_model=List[BankCapitalResponse])
async def get_all_bank_capital(
    is_active: Optional[bool] = None,
    is_partner: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Получить капитал всех банков в системе
    
    Фильтры:
    - is_active: только активные банки
    - is_partner: только партнёрские банки
    """
    try:
        query = db.query(BankCapital)
        
        if is_active is not None:
            query = query.filter(BankCapital.is_active == is_active)
        
        if is_partner is not None:
            query = query.filter(BankCapital.is_partner == is_partner)
        
        banks = query.all()
        
        # Если нет данных, создаем демо-данные
        if not banks:
            logger.info("No bank capital data found, creating demo data")
            demo_banks = [
                BankCapital(
                    bank_code="vbank",
                    bank_name="Virtual Bank",
                    total_capital=Decimal("15000000000.00"),  # 15 млрд
                    tier1_capital=Decimal("12000000000.00"),
                    tier2_capital=Decimal("3000000000.00"),
                    total_assets=Decimal("100000000000.00"),  # 100 млрд
                    total_liabilities=Decimal("85000000000.00"),
                    capital_adequacy_ratio=Decimal("15.00"),
                    liquidity_ratio=Decimal("45.00"),
                    max_loan_amount=Decimal("500000000.00"),
                    interbank_limit=Decimal("10000000000.00"),
                    is_active=True,
                    is_partner=True,
                    last_audit_date=datetime(2024, 10, 15)
                ),
                BankCapital(
                    bank_code="abank",
                    bank_name="Awesome Bank",
                    total_capital=Decimal("12000000000.00"),
                    tier1_capital=Decimal("9500000000.00"),
                    tier2_capital=Decimal("2500000000.00"),
                    total_assets=Decimal("80000000000.00"),
                    total_liabilities=Decimal("68000000000.00"),
                    capital_adequacy_ratio=Decimal("15.00"),
                    liquidity_ratio=Decimal("42.00"),
                    max_loan_amount=Decimal("400000000.00"),
                    interbank_limit=Decimal("8000000000.00"),
                    is_active=True,
                    is_partner=True,
                    last_audit_date=datetime(2024, 10, 20)
                ),
                BankCapital(
                    bank_code="sbank",
                    bank_name="Smart Bank",
                    total_capital=Decimal("10000000000.00"),
                    tier1_capital=Decimal("8000000000.00"),
                    tier2_capital=Decimal("2000000000.00"),
                    total_assets=Decimal("65000000000.00"),
                    total_liabilities=Decimal("55000000000.00"),
                    capital_adequacy_ratio=Decimal("15.38"),
                    liquidity_ratio=Decimal("48.00"),
                    max_loan_amount=Decimal("300000000.00"),
                    interbank_limit=Decimal("6000000000.00"),
                    is_active=True,
                    is_partner=True,
                    last_audit_date=datetime(2024, 10, 25)
                ),
            ]
            
            for bank in demo_banks:
                db.add(bank)
            
            try:
                db.commit()
                banks = demo_banks
                logger.info("Demo bank capital data created successfully")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to create demo data: {str(e)}")
                return []
        
        return [BankCapitalResponse.from_orm(bank) for bank in banks]
    
    except HTTPException:
        raise
    except Exception as e:
        handle_database_error(e, "получение данных о капитале банков")


@router.get("/{bank_code}", response_model=BankCapitalResponse)
async def get_bank_capital(
    bank_code: str,
    db: Session = Depends(get_db)
):
    """Получить капитал конкретного банка по коду"""
    try:
        bank = db.query(BankCapital).filter(BankCapital.bank_code == bank_code).first()
        
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Банк с кодом '{bank_code}' не найден в системе"
            )
        
        return BankCapitalResponse.from_orm(bank)
    
    except HTTPException:
        raise
    except Exception as e:
        handle_database_error(e, f"получение данных о капитале банка '{bank_code}'")


@router.post("/", response_model=BankCapitalResponse, status_code=status.HTTP_201_CREATED)
async def create_bank_capital(
    data: BankCapitalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создать запись о капитале банка (только для администраторов)"""
    try:
        # Проверка существования
        existing = db.query(BankCapital).filter(BankCapital.bank_code == data.bank_code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Банк с кодом '{data.bank_code}' уже существует"
            )
        
        bank = BankCapital(**data.dict())
        db.add(bank)
        db.commit()
        db.refresh(bank)
        
        logger.info(f"Bank capital created for {data.bank_code} by user {current_user.id}")
        return BankCapitalResponse.from_orm(bank)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "создание данных о капитале банка")


@router.patch("/{bank_code}", response_model=BankCapitalResponse)
async def update_bank_capital(
    bank_code: str,
    data: BankCapitalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить данные о капитале банка"""
    try:
        bank = db.query(BankCapital).filter(BankCapital.bank_code == bank_code).first()
        
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Банк с кодом '{bank_code}' не найден"
            )
        
        # Обновляем только переданные поля
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bank, field, value)
        
        db.commit()
        db.refresh(bank)
        
        logger.info(f"Bank capital updated for {bank_code} by user {current_user.id}")
        return BankCapitalResponse.from_orm(bank)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, f"обновление данных о капитале банка '{bank_code}'")


@router.delete("/{bank_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank_capital(
    bank_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить данные о капитале банка"""
    try:
        bank = db.query(BankCapital).filter(BankCapital.bank_code == bank_code).first()
        
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Банк с кодом '{bank_code}' не найден"
            )
        
        db.delete(bank)
        db.commit()
        
        logger.info(f"Bank capital deleted for {bank_code} by user {current_user.id}")
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, f"удаление данных о капитале банка '{bank_code}'")

