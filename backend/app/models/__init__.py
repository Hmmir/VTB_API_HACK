"""Database models."""
from app.models.user import User
from app.models.bank_connection import BankConnection
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.bank_product import BankProduct
from app.models.recommendation import Recommendation
from app.models.consent import (
    PartnerBank,
    ConsentRequest,
    Consent,
    ConsentEvent,
    ConsentStatus,
    ConsentScope,
)
from app.models.payment import (
    Payment,
    PaymentType,
    PaymentStatus,
    InterbankTransfer,
    InterbankTransferStatus,
)
from app.models.product_agreement import (
    ProductAgreement,
    ProductType,
    AgreementStatus,
    PaymentScheduleType,
    PaymentSchedule,
    AgreementEvent,
)
from app.models.notification import (
    Notification,
    NotificationType,
    NotificationPriority,
)
from app.models.key_rate import KeyRateHistory
from app.models.bank_capital import BankCapital

__all__ = [
    "User",
    "BankConnection",
    "Account",
    "Transaction",
    "Category",
    "Budget",
    "Goal",
    "BankProduct",
    "Recommendation",
    "PartnerBank",
    "ConsentRequest",
    "Consent",
    "ConsentEvent",
    "ConsentStatus",
    "ConsentScope",
    "Payment",
    "PaymentType",
    "PaymentStatus",
    "InterbankTransfer",
    "InterbankTransferStatus",
    "ProductAgreement",
    "ProductType",
    "AgreementStatus",
    "PaymentScheduleType",
    "PaymentSchedule",
    "AgreementEvent",
    "Notification",
    "NotificationType",
    "NotificationPriority",
    "KeyRateHistory",
    "BankCapital",
]

