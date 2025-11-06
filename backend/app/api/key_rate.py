"""Key Rate API - История ключевой ставки ЦБ РФ"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

from ..database import get_db
from ..models import KeyRateHistory

router = APIRouter(prefix="/api/v1/key-rate", tags=["Key Rate"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class KeyRateResponse(BaseModel):
    id: int
    effective_date: datetime
    rate: float
    decision_date: Optional[datetime]
    source: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class KeyRateCurrentResponse(BaseModel):
    current_rate: float
    effective_date: datetime
    source: Optional[str]


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/current", response_model=KeyRateCurrentResponse)
async def get_current_key_rate(db: Session = Depends(get_db)):
    """
    Получить текущую ключевую ставку ЦБ РФ
    
    Возвращает последнюю действующую ключевую ставку.
    """
    try:
        # Получаем последнюю ставку
        latest_rate = db.query(KeyRateHistory).order_by(
            desc(KeyRateHistory.effective_date)
        ).first()
        
        if not latest_rate:
            # Если нет данных, возвращаем текущую ставку ЦБ (21% на ноябрь 2024)
            return KeyRateCurrentResponse(
                current_rate=21.00,
                effective_date=datetime(2024, 10, 28),
                source="cbr.ru (default)"
            )
        
        return KeyRateCurrentResponse(
            current_rate=float(latest_rate.rate),
            effective_date=latest_rate.effective_date,
            source=latest_rate.source
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch current key rate: {str(e)}")


@router.get("/history", response_model=List[KeyRateResponse])
async def get_key_rate_history(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Получить историю изменений ключевой ставки ЦБ РФ
    
    Parameters:
    - limit: Количество записей (по умолчанию 10)
    - offset: Смещение для пагинации (по умолчанию 0)
    
    Возвращает список изменений ключевой ставки в обратном хронологическом порядке.
    """
    try:
        history = db.query(KeyRateHistory).order_by(
            desc(KeyRateHistory.effective_date)
        ).offset(offset).limit(limit).all()
        
        # Если нет данных, создаем примерные данные для демонстрации
        if not history and offset == 0:
            # История ключевой ставки ЦБ РФ (реальные данные 2024)
            demo_history = [
                KeyRateHistory(
                    id=1,
                    effective_date=datetime(2024, 10, 28),
                    rate=Decimal("21.00"),
                    decision_date=datetime(2024, 10, 25),
                    source="cbr.ru",
                    notes="Повышение ставки для сдерживания инфляции"
                ),
                KeyRateHistory(
                    id=2,
                    effective_date=datetime(2024, 9, 16),
                    rate=Decimal("19.00"),
                    decision_date=datetime(2024, 9, 13),
                    source="cbr.ru",
                    notes="Повышение ставки"
                ),
                KeyRateHistory(
                    id=3,
                    effective_date=datetime(2024, 7, 26),
                    rate=Decimal("18.00"),
                    decision_date=datetime(2024, 7, 26),
                    source="cbr.ru",
                    notes="Повышение ставки"
                ),
                KeyRateHistory(
                    id=4,
                    effective_date=datetime(2024, 6, 7),
                    rate=Decimal("16.00"),
                    decision_date=datetime(2024, 6, 7),
                    source="cbr.ru",
                    notes="Сохранение ставки"
                ),
                KeyRateHistory(
                    id=5,
                    effective_date=datetime(2024, 2, 16),
                    rate=Decimal("16.00"),
                    decision_date=datetime(2024, 2, 16),
                    source="cbr.ru",
                    notes="Повышение ставки до 16%"
                ),
            ]
            
            # Добавляем в БД
            for rate in demo_history:
                db.add(rate)
            
            try:
                db.commit()
                # Перезагружаем данные
                history = db.query(KeyRateHistory).order_by(
                    desc(KeyRateHistory.effective_date)
                ).offset(offset).limit(limit).all()
            except:
                db.rollback()
                # Если не удалось сохранить, возвращаем demo данные
                return [KeyRateResponse.from_orm(rate) for rate in demo_history[:limit]]
        
        return [KeyRateResponse.from_orm(rate) for rate in history]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch key rate history: {str(e)}")

