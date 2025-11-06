"""Bank Capital Model - Капитал банков"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean
from sqlalchemy.sql import func
from decimal import Decimal
from app.database import Base


class BankCapital(Base):
    """Капитал и финансовые показатели банков в системе"""
    __tablename__ = "bank_capital"
    
    id = Column(Integer, primary_key=True, index=True)
    bank_code = Column(String(50), nullable=False, unique=True, index=True, comment="Код банка")
    bank_name = Column(String(255), nullable=False, comment="Название банка")
    
    # Капитал
    total_capital = Column(Numeric(20, 2), nullable=False, default=Decimal("0.00"), comment="Общий капитал")
    tier1_capital = Column(Numeric(20, 2), nullable=False, default=Decimal("0.00"), comment="Капитал 1 уровня")
    tier2_capital = Column(Numeric(20, 2), nullable=False, default=Decimal("0.00"), comment="Капитал 2 уровня")
    
    # Активы и обязательства
    total_assets = Column(Numeric(20, 2), nullable=False, default=Decimal("0.00"), comment="Всего активов")
    total_liabilities = Column(Numeric(20, 2), nullable=False, default=Decimal("0.00"), comment="Всего обязательств")
    
    # Коэффициенты
    capital_adequacy_ratio = Column(Numeric(5, 2), nullable=True, comment="Норматив достаточности капитала (%)")
    liquidity_ratio = Column(Numeric(5, 2), nullable=True, comment="Норматив ликвидности (%)")
    
    # Лимиты
    max_loan_amount = Column(Numeric(20, 2), nullable=True, comment="Максимальная сумма кредита")
    interbank_limit = Column(Numeric(20, 2), nullable=True, comment="Лимит межбанковских операций")
    
    # Статус
    is_active = Column(Boolean, default=True, comment="Активен ли банк")
    is_partner = Column(Boolean, default=False, comment="Партнёрский банк")
    
    # Метаданные
    last_audit_date = Column(DateTime, nullable=True, comment="Дата последнего аудита")
    notes = Column(String(1000), nullable=True, comment="Примечания")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<BankCapital(bank={self.bank_code}, capital={self.total_capital})>"
    
    @property
    def capital_adequacy_percentage(self) -> float:
        """Рассчитать норматив достаточности капитала"""
        if self.total_assets and self.total_assets > 0:
            return float((self.total_capital / self.total_assets) * 100)
        return 0.0
    
    @property
    def leverage_ratio(self) -> float:
        """Рассчитать коэффициент левереджа"""
        if self.total_assets and self.total_assets > 0:
            return float(self.total_liabilities / self.total_assets)
        return 0.0

