"""GOST-шлюз API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
import os

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.config import settings

router = APIRouter(prefix="/gost", tags=["GOST"])
logger = logging.getLogger(__name__)


def get_gost_client():
    """Получить настроенный GOST клиент"""
    # Проверяем что GOSTClient доступен
    try:
        from app.integrations.gost_client_new import GOSTClient
        
        if not settings.GOST_CLIENT_ID or not settings.GOST_CLIENT_SECRET:
            raise HTTPException(
                status_code=500,
                detail="GOST credentials not configured"
            )
        
        client = GOSTClient(
            client_id=settings.GOST_CLIENT_ID,
            client_secret=settings.GOST_CLIENT_SECRET,
            cert_name=settings.GOST_CERT_NAME or "GOST Certificate",
            auth_url=settings.AUTH_API_URL,
            api_url=settings.BANKING_API_URL,
            gost_url=settings.GOST_API_BASE,
            csptest_path=settings.GOST_CSPTEST_PATH
        )
        return client
    except ImportError as e:
        logger.error(f"GOSTClient not available: {e}")
        raise HTTPException(
            status_code=500,
            detail="GOST client not installed. This feature requires CryptoPro CSP."
        )
    except Exception as e:
        logger.error(f"Failed to initialize GOST client: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize GOST client: {str(e)}"
        )


@router.get("/status")
async def get_gost_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Получить статус GOST-подключения
    
    Returns:
        {
            "enabled": bool,
            "configured": bool,
            "endpoint": str,
            "client_id": str
        }
    """
    # Проверка доступности CryptoPro
    csptest_exists = os.path.exists(settings.GOST_CSPTEST_PATH)
    
    return {
        "enabled": settings.USE_GOST,
        "configured": bool(settings.GOST_CLIENT_ID and settings.GOST_CLIENT_SECRET),
        "endpoint": settings.GOST_API_BASE,
        "client_id": settings.GOST_CLIENT_ID,
        "cert_configured": bool(settings.GOST_CERT_NAME),
        "csptest_available": csptest_exists,
        "csptest_path": settings.GOST_CSPTEST_PATH if csptest_exists else None
    }


@router.post("/test")
async def test_gost_connection(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Протестировать GOST TLS подключение
    
    Returns:
        {
            "success": bool,
            "cipher": str,
            "server": str,
            "time": float,
            "message": str
        }
    """
    try:
        # Попытка вызвать Windows service (если запущен на хосте)
        import requests
        try:
            logger.info("Вызов GOST Windows Service на хосте...")
            response = requests.post(
                "http://host.docker.internal:5555/test",
                timeout=35
            )
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ GOST test через Windows service: success={result.get('success')}")
                return result
            else:
                logger.warning(f"Windows service вернул {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.warning("Windows service недоступен, пробуем через Docker контейнер...")
        except Exception as e:
            logger.warning(f"Ошибка при вызове Windows service: {e}")
        
        # Fallback: попытка через Docker (не сработает на Windows, но попробуем)
        client = get_gost_client()
        result = client.test_gost(verbose=True)
        
        if result.get("success"):
            message = f"✅ GOST TLS успешно! Сервер: {result.get('server', 'N/A')}, Cipher: {result.get('cipher', 'N/A')}"
        else:
            message = f"❌ GOST TLS не работает: {result.get('error', 'Unknown error')}"
        
    return {
            **result,
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GOST test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Ошибка теста: {str(e)}"
        }


@router.post("/health")
async def gost_health_check(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Полная проверка здоровья GOST компонентов
    
    Returns:
        {
            "auth": bool,
            "standard_api": bool,
            "gost_tls": bool,
            "overall": str
        }
    """
    try:
        client = get_gost_client()
        results = client.health_check()
        
        # Определить общий статус
        if all(results.values()):
            overall = "healthy"
        elif results.get("auth") and results.get("gost_tls"):
            overall = "partial"
        else:
            overall = "unhealthy"
        
        return {
            **results,
            "overall": overall,
            "message": f"Auth: {'✅' if results['auth'] else '❌'} | "
                      f"Standard API: {'✅' if results['standard_api'] else '❌'} | "
                      f"GOST TLS: {'✅' if results['gost_tls'] else '❌'}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
                return {
            "auth": False,
            "standard_api": False,
            "gost_tls": False,
            "overall": "error",
            "error": str(e),
            "message": f"❌ Ошибка проверки: {str(e)}"
        }


@router.get("/accounts")
async def get_gost_accounts(
    use_gost: bool = True,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Получить счета через GOST API
    
    Args:
        use_gost: Использовать GOST TLS (default: True)
    
    Returns:
        Список счетов от API Registry
    """
    try:
        client = get_gost_client()
        result = client.get_accounts(use_gost=use_gost)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get GOST accounts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get accounts: {str(e)}"
        )


@router.get("/accounts/{account_id}/transactions")
async def get_gost_transactions(
    account_id: str,
    use_gost: bool = True,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Получить транзакции через GOST API
    
    Args:
        account_id: ID счета
        use_gost: Использовать GОСТ TLS (default: True)
    
    Returns:
        Список транзакций от API Registry
    """
    try:
        client = get_gost_client()
        result = client.get_transactions(account_id, use_gost=use_gost)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get GOST transactions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get transactions: {str(e)}"
        )


@router.get("/cards")
async def get_gost_cards(
    use_gost: bool = True,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Получить карты через GOST API
    
    Args:
        use_gost: Использовать GOST TLS (default: True)
    
    Returns:
        Список карт от API Registry
    """
    try:
        client = get_gost_client()
        result = client.get_cards(use_gost=use_gost)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get GOST cards: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cards: {str(e)}"
        )
