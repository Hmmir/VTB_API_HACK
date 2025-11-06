"""
Banker API - управление банком для сотрудников
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import User, BankConnection, Account, Transaction, Consent, BankProduct
from .dependencies import get_current_user

router = APIRouter(prefix="/api/v1/banker", tags=["Banker"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class BankStatistics(BaseModel):
    total_clients: int
    total_accounts: int
    total_balance: float
    total_transactions: int
    active_consents: int
    active_agreements: int


class ClientInfo(BaseModel):
    id: int
    email: str
    full_name: str | None
    created_at: str
    total_accounts: int
    total_balance: float
    active_connections: int


class ProductCreate(BaseModel):
    name: str
    type: str
    min_amount: float
    max_amount: float
    interest_rate: float
    term_months: int


class ProductUpdate(BaseModel):
    interest_rate: float | None = None
    is_active: bool | None = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/statistics", response_model=BankStatistics)
async def get_bank_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить статистику банка
    
    Требует авторизацию.
    """
    try:
        # Всего клиентов (уникальных пользователей с подключениями)
        total_clients = db.query(User).count()
        
        # Всего счетов
        total_accounts = db.query(Account).count()
        
        # Общий баланс
        total_balance = db.query(func.sum(Account.balance)).scalar() or 0
        
        # Всего транзакций
        total_transactions = db.query(Transaction).count()
        
        # Активные согласия
        active_consents = db.query(Consent).filter(
            Consent.status == "active"
        ).count()
        
        # Активные договоры (продукты)
        # TODO: Implement when ProductAgreement model is available
        active_agreements = 0
        
        return BankStatistics(
            total_clients=total_clients,
            total_accounts=total_accounts,
            total_balance=float(total_balance),
            total_transactions=total_transactions,
            active_consents=active_consents,
            active_agreements=active_agreements
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")


@router.get("/clients", response_model=dict)
async def get_clients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить список всех клиентов банка
    
    Требует авторизацию.
    """
    try:
        users = db.query(User).all()
        
        clients = []
        for user in users:
            # Подсчитываем счета
            accounts = db.query(Account).join(BankConnection).filter(
                BankConnection.user_id == user.id
            ).all()
            
            total_accounts = len(accounts)
            total_balance = sum(float(acc.balance) for acc in accounts)
            
            # Подсчитываем активные подключения
            active_connections = db.query(BankConnection).filter(
                BankConnection.user_id == user.id,
                BankConnection.status == "active"
            ).count()
            
            clients.append(ClientInfo(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                created_at=user.created_at.isoformat(),
                total_accounts=total_accounts,
                total_balance=total_balance,
                active_connections=active_connections
            ))
        
        return {"clients": clients, "total": len(clients)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch clients: {str(e)}")


@router.post("/products", response_model=dict)
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Создать новый банковский продукт
    
    Требует авторизацию.
    """
    try:
        # Проверяем существует ли модель BankProduct
        # Если нет - создаем простую заглушку
        new_product = {
            "id": 1,  # TODO: Auto-increment
            "name": product.name,
            "type": product.type,
            "min_amount": product.min_amount,
            "max_amount": product.max_amount,
            "interest_rate": product.interest_rate,
            "term_months": product.term_months,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        return new_product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")


@router.put("/products/{product_id}", response_model=dict)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновить параметры продукта (ставку, статус)
    
    Требует авторизацию.
    """
    try:
        # TODO: Implement actual product update when BankProduct model is available
        return {
            "id": product_id,
            "updated_at": datetime.now().isoformat(),
            "changes": product_update.dict(exclude_unset=True)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")


@router.get("/consents", response_model=dict)
async def get_all_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить все согласия клиентов (для банкира)
    
    Требует авторизацию.
    """
    try:
        consents = db.query(Consent).all()
        
        return {
            "consents": [
                {
                    "id": str(consent.id),
                    "user_id": consent.user_id,
                    "partner_bank_id": consent.partner_bank_id,
                    "scopes": consent.scopes,
                    "status": consent.status,
                    "valid_until": consent.valid_until.isoformat(),
                    "granted_at": consent.granted_at.isoformat() if consent.granted_at else None
                }
                for consent in consents
            ],
            "total": len(consents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch consents: {str(e)}")

