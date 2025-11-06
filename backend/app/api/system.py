"""System information and configuration endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.bank_connection import BankConnection
from app.database import get_db


router = APIRouter(prefix="/system", tags=["System"])


class SystemInfoResponse(BaseModel):
    """System information response."""
    app_name: str
    app_version: str
    use_gost: bool
    gost_api_base: str
    supported_banks: list[str]
    features: Dict[str, bool]


@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info(current_user: User = Depends(get_current_user)):
    """Get system configuration and features.
    
    Requires authentication.
    
    Returns information about:
    - GOST gateway usage
    - Supported banks
    - Available features
    """
    return SystemInfoResponse(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        use_gost=settings.USE_GOST,
        gost_api_base=settings.GOST_API_BASE if settings.USE_GOST else "",
        supported_banks=["vbank", "abank", "sbank"],
        features={
            "gost_gateway": settings.USE_GOST,
            "multi_bank_aggregation": True,
            "auto_categorization": True,
            "analytics": True,
            "budgets": True,
            "goals": True,
            "product_comparison": True,
            "csv_export": True,
            "pwa": True,
        }
    )


@router.get("/admin-stats")
async def get_admin_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get admin statistics from database.
    
    Returns real statistics about:
    - Total users
    - Total bank connections
    - Total accounts
    - Total transactions
    """
    # Count users
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # Count bank connections
    total_connections = db.query(func.count(BankConnection.id)).scalar() or 0
    
    # Count accounts
    total_accounts = db.query(func.count(Account.id)).scalar() or 0
    
    # Count transactions
    total_transactions = db.query(func.count(Transaction.id)).scalar() or 0
    
    return {
        "users": total_users,
        "banks": 3,  # vbank, abank, sbank
        "connections": total_connections,
        "accounts": total_accounts,
        "transactions": total_transactions,
    }


@router.get("/gost-status")
async def get_gost_status(current_user: User = Depends(get_current_user)):
    """Get GOST gateway status.
    
    Requires authentication.
    
    Returns:
        Dict with GOST configuration and compliance info
    """
    return {
        "enabled": settings.USE_GOST,
        "gateway_url": settings.GOST_API_BASE if settings.USE_GOST else None,
        "compliance": {
            "gost_r_34_10_2012": settings.USE_GOST,  # Digital signature standard
            "gost_r_34_11_2012": settings.USE_GOST,  # Hash function standard
            "tls_gost": settings.USE_GOST,
        },
        "description": (
            "GOST Gateway provides cryptographic protection according to "
            "Russian GOST R 34.10-2012 and GOST R 34.11-2012 standards. "
            "This ensures compliance with Central Bank of Russia requirements."
        ) if settings.USE_GOST else "Standard TLS connection",
        "benefits": [
            "Compliance with CBR (Central Bank of Russia) requirements",
            "GOST R 34.10-2012 digital signatures",
            "GOST R 34.11-2012 hash algorithms",
            "Production-ready for Russian financial institutions",
        ] if settings.USE_GOST else []
    }

