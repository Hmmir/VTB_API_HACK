"""Key Rate History Model - История ключевой ставки ЦБ РФ"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric
from sqlalchemy.sql import func
from decimal import Decimal
from app.database import Base


class KeyRateHistory(Base):
    """История изменений ключевой ставки ЦБ РФ"""
    __tablename__ = "key_rate_history"
    
    id = Column(Integer, primary_key=True, index=True)
    effective_date = Column(DateTime, nullable=False, unique=True, index=True, comment="Дата вступления в силу")
    rate = Column(Numeric(5, 2), nullable=False, comment="Ключевая ставка (%)")
    decision_date = Column(DateTime, nullable=True, comment="Дата решения Совета Директоров")
    source = Column(String(255), nullable=True, comment="Источник (например, cbr.ru)")
    notes = Column(String(1000), nullable=True, comment="Примечания")
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<KeyRateHistory(date={self.effective_date}, rate={self.rate}%)>"

