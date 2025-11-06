"""
Unified Banking API
Объединяет VTB API (3 банка) + Banking API стенд организаторов с GOST
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import httpx
import os
import logging

from ..database import get_db
from ..models import User, BankConnection
from .dependencies import get_current_user

router = APIRouter(prefix="/unified-banking", tags=["Unified Banking"])
logger = logging.getLogger(__name__)


@router.get("/accounts/all")
async def get_all_accounts(
    use_gost: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получить счета из ВСЕХ источников:
    1. VTB API (3 банка: Virtual, Awesome, Smart)
    2. Banking API стенд организаторов (с GOST или без)
    
    Args:
        use_gost: Использовать GOST API для Banking API
    """
    
    result = {
        "vtb_banks": [],
        "banking_api_accounts": [],
        "total_accounts": 0,
        "total_balance": 0.0,
        "gost_used": use_gost
    }
    
    # 1. Получить счета из VTB API (3 банка)
    logger.info(f"[Unified] Getting VTB accounts for user {current_user.id}")
    
    vtb_connections = db.query(BankConnection).filter(
        BankConnection.user_id == current_user.id,
        BankConnection.is_active == True
    ).all()
    
    vtb_team_id = os.getenv("VTB_TEAM_ID", "team075")
    vtb_secret = os.getenv("VTB_TEAM_SECRET", "")
    vtb_api_url = os.getenv("VTB_API_BASE_URL", "https://ift.rtuitlab.dev")
    
    for conn in vtb_connections:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get accounts from VTB API
                response = await client.get(
                    f"{vtb_api_url}/api/Connection/GetAccounts",
                    headers={
                        "TeamId": vtb_team_id,
                        "TeamSecret": vtb_secret
                    },
                    params={
                        "connectionId": conn.external_connection_id
                    }
                )
                
                if response.status_code == 200:
                    accounts_data = response.json()
                    
                    bank_info = {
                        "bank_code": conn.bank_code,
                        "bank_name": conn.bank_name,
                        "source": "VTB_API",
                        "accounts": []
                    }
                    
                    for acc in accounts_data:
                        account_info = {
                            "account_id": acc.get("accountId"),
                            "account_number": acc.get("accountNumber"),
                            "balance": float(acc.get("balance", 0)),
                            "currency": acc.get("currency", "RUB"),
                            "type": acc.get("accountType", "current")
                        }
                        bank_info["accounts"].append(account_info)
                        result["total_balance"] += account_info["balance"]
                        result["total_accounts"] += 1
                    
                    result["vtb_banks"].append(bank_info)
                    logger.info(f"[Unified] Got {len(bank_info['accounts'])} accounts from {conn.bank_code}")
                    
        except Exception as e:
            logger.error(f"[Unified] Error getting VTB accounts for {conn.bank_code}: {e}")
    
    # 2. Получить счета из Banking API стенд (с GOST или без)
    logger.info(f"[Unified] Getting Banking API accounts (GOST: {use_gost})")
    
    try:
        # Get OAuth token
        auth_url = os.getenv("AUTH_API_URL", "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token")
        client_id = os.getenv("VTB_TEAM_ID", "team075")
        client_secret = os.getenv("VTB_TEAM_SECRET", "")
        
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            auth_response = await client.post(
                auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret
                }
            )
            
            if auth_response.status_code == 200:
                token_data = auth_response.json()
                access_token = token_data.get("access_token")
                
                # Choose API endpoint based on GOST flag
                if use_gost:
                    api_url = os.getenv("GOST_API_URL", "https://api.gost.bankingapi.ru:8443")
                else:
                    api_url = os.getenv("BANKING_API_URL", "https://api.bankingapi.ru")
                
                # Try to get accounts from Banking API
                # Note: May need specific endpoints after registration
                result["banking_api_accounts"].append({
                    "source": "BANKING_API_GOST" if use_gost else "BANKING_API_STANDARD",
                    "status": "configured",
                    "token_obtained": True,
                    "note": "Requires API registration at https://api-registry-frontend.bankingapi.ru/"
                })
                
                logger.info(f"[Unified] Banking API token obtained, endpoint: {api_url}")
            
    except Exception as e:
        logger.error(f"[Unified] Error getting Banking API accounts: {e}")
        result["banking_api_accounts"].append({
            "source": "BANKING_API",
            "status": "error",
            "error": str(e)
        })
    
    return result


@router.post("/transfer/unified")
async def unified_transfer(
    from_account_id: str,
    to_account_id: str,
    amount: float,
    use_gost: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Универсальный перевод между счетами из ЛЮБЫХ источников:
    - VTB API (между 3 банками)
    - Banking API (с GOST или без)
    - Кросс-API переводы
    
    Args:
        from_account_id: ID счета-отправителя
        to_account_id: ID счета-получателя
        amount: Сумма перевода
        use_gost: Использовать GOST для Banking API
    """
    
    logger.info(f"[Unified Transfer] {from_account_id} -> {to_account_id}: {amount} (GOST: {use_gost})")
    
    result = {
        "success": False,
        "from_account": from_account_id,
        "to_account": to_account_id,
        "amount": amount,
        "gost_used": False,
        "transfer_route": ""
    }
    
    try:
        # Determine source and target systems
        # VTB accounts format: "vtb_{bank_code}_{account_id}"
        # Banking API format: "banking_{account_id}"
        
        is_from_vtb = from_account_id.startswith("vtb_")
        is_to_vtb = to_account_id.startswith("vtb_")
        
        vtb_team_id = os.getenv("VTB_TEAM_ID", "team075")
        vtb_secret = os.getenv("VTB_TEAM_SECRET", "")
        vtb_api_url = os.getenv("VTB_API_BASE_URL", "https://ift.rtuitlab.dev")
        
        # Case 1: VTB -> VTB (between 3 banks)
        if is_from_vtb and is_to_vtb:
            logger.info("[Unified Transfer] VTB to VTB transfer")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{vtb_api_url}/api/Transfer/Create",
                    headers={
                        "TeamId": vtb_team_id,
                        "TeamSecret": vtb_secret,
                        "Content-Type": "application/json"
                    },
                    json={
                        "fromAccountId": from_account_id.replace("vtb_", ""),
                        "toAccountId": to_account_id.replace("vtb_", ""),
                        "amount": amount,
                        "currency": "RUB"
                    }
                )
                
                if response.status_code == 200:
                    result["success"] = True
                    result["transfer_route"] = "VTB_API"
                    result["transaction_id"] = response.json().get("transferId")
                    logger.info(f"[Unified Transfer] VTB transfer successful: {result['transaction_id']}")
                else:
                    raise HTTPException(status_code=400, detail=f"VTB transfer failed: {response.text}")
        
        # Case 2: Banking API -> Banking API (with GOST option)
        elif not is_from_vtb and not is_to_vtb:
            logger.info(f"[Unified Transfer] Banking API transfer (GOST: {use_gost})")
            
            # Get OAuth token
            auth_url = os.getenv("AUTH_API_URL", "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token")
            client_id = os.getenv("VTB_TEAM_ID", "team075")
            client_secret = os.getenv("VTB_TEAM_SECRET", "")
            
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                auth_response = await client.post(
                    auth_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": client_id,
                        "client_secret": client_secret
                    }
                )
                
                if auth_response.status_code == 200:
                    token_data = auth_response.json()
                    access_token = token_data.get("access_token")
                    
                    # Choose API based on GOST flag
                    if use_gost:
                        api_url = os.getenv("GOST_API_URL", "https://api.gost.bankingapi.ru:8443")
                        result["gost_used"] = True
                        result["transfer_route"] = "BANKING_API_GOST"
                    else:
                        api_url = os.getenv("BANKING_API_URL", "https://api.bankingapi.ru")
                        result["transfer_route"] = "BANKING_API_STANDARD"
                    
                    # Note: Actual transfer endpoint depends on registered APIs
                    # This is a template that needs to be adjusted after API registration
                    result["success"] = True
                    result["note"] = "Banking API transfer configured. Requires API endpoint registration."
                    result["token_obtained"] = True
                    
                    logger.info(f"[Unified Transfer] Banking API ready: {api_url}")
        
        # Case 3: Cross-API transfer (VTB <-> Banking API)
        else:
            logger.info("[Unified Transfer] Cross-API transfer (VTB <-> Banking API)")
            
            result["transfer_route"] = "CROSS_API"
            result["note"] = "Cross-API transfer requires both systems to support it"
            
            # This would require:
            # 1. Withdraw from source
            # 2. Deposit to target
            # Implementation depends on both APIs supporting external transfers
        
        return result
        
    except Exception as e:
        logger.error(f"[Unified Transfer] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transfer failed: {str(e)}")


@router.get("/sources")
async def get_available_sources() -> Dict[str, Any]:
    """
    Получить список всех доступных источников данных (публичный endpoint)
    
    ВАЖНО: ГОСТ - это НЕ отдельный банк, а протокол шифрования!
    ГОСТ можно включить для любого банка из Banking API.
    """
    
    return {
        "sources": [
            {
                "id": "vtb_api",
                "name": "VTB API - Песочница",
                "description": "3 симулированных банка для тестирования",
                "banks": [
                    {"code": "vbank", "name": "Virtual Bank", "icon": "💜"},
                    {"code": "abank", "name": "Awesome Bank", "icon": "🟢"},
                    {"code": "sbank", "name": "Smart Bank", "icon": "🔵"}
                ],
                "status": "active",
                "features": ["accounts", "transactions", "transfers", "multi-bank"],
                "endpoint": os.getenv("VTB_API_BASE_URL", "https://ift.rtuitlab.dev"),
                "gost_support": False
            },
            {
                "id": "banking_api",
                "name": "Banking API - Стенд организаторов",
                "description": "Реальные банковские API с поддержкой ГОСТ",
                "banks": "Depends on API registration",
                "status": "configured",
                "features": ["accounts", "payments", "cards", "consents"],
                "endpoint": os.getenv("BANKING_API_URL", "https://api.bankingapi.ru"),
                "gost_support": True,
                "gost_endpoint": os.getenv("GOST_API_URL", "https://api.gost.bankingapi.ru:8443"),
                "requires": "API registration at https://api-registry-frontend.bankingapi.ru/"
            }
        ],
        "gost_info": {
            "description": "ГОСТ - это протокол криптографического шифрования, а НЕ банк!",
            "usage": "Включите ГОСТ для использования отечественных криптоалгоритмов при работе с Banking API",
            "requirements": [
                "OpenSSL с поддержкой ГОСТ",
                "curl с поддержкой ГОСТ",
                "Сертификат КриптоПРО"
            ],
            "standards": [
                "ГОСТ Р 34.10-2012 (ЭЦП)",
                "ГОСТ Р 34.11-2012 (Хеширование)",
                "TLS over HTTPS с ГОСТ-шифрами"
            ],
            "toggle": "use_gost=true parameter for Banking API calls"
        }
    }

