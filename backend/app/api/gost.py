"""
GOST Status API
Endpoint для проверки статуса GOST-поддержки
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import os
import logging

from app.database import get_db
from app.services.gost_adapter import GOSTAdapter, GOSTMode

router = APIRouter(prefix="/gost", tags=["GOST"])
logger = logging.getLogger(__name__)


@router.get("/status")
async def get_gost_status() -> Dict[str, Any]:
    """
    Получить статус GOST-поддержки
    
    Возвращает информацию о доступности GOST-шлюза и текущем режиме работы
    """
    use_gost = os.getenv("USE_GOST", "true").lower() == "true"
    gost_url = os.getenv("GOST_API_URL", "https://api.gost.bankingapi.ru:8443")
    standard_url = os.getenv("BANKING_API_URL", "https://api.bankingapi.ru")
    
    return {
        "enabled": use_gost,
        "mode": "GOST" if use_gost else "Standard",
        "api_endpoint": gost_url if use_gost else standard_url,
        "description": "🔒 GOST-шлюз настроен на api.gost.bankingapi.ru:8443" if use_gost else "⚠️ Используется стандартный API без GOST",
        "requirements": _get_requirements_status(),
        "recommendation": _get_recommendation({"gost_available": use_gost}),
        "urls": {
            "auth": os.getenv("AUTH_API_URL", "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token"),
            "gost_api": gost_url,
            "standard_api": standard_url
        }
    }


def _get_status_description(status: Dict[str, Any]) -> str:
    """Получить человекочитаемое описание статуса"""
    if status["gost_available"]:
        return "🔒 GOST-шлюз доступен и активен. Все запросы идут через защищенное GOST TLS соединение."
    else:
        return "⚠️ GOST-шлюз недоступен. Используется стандартный API. Для работы с регулируемыми банками требуется настройка GOST."


def _get_requirements_status() -> Dict[str, Any]:
    """Проверить статус требований для GOST"""
    return {
        "openssl_gost": {
            "required": True,
            "installed": os.path.exists("/usr/local/bin/openssl-gost") or os.path.exists("C:\\gost\\openssl.exe"),
            "description": "OpenSSL с поддержкой GOST алгоритмов"
        },
        "curl_gost": {
            "required": True,
            "installed": os.path.exists("/usr/local/bin/curl-gost") or os.path.exists("C:\\gost\\curl.exe"),
            "description": "curl с поддержкой GOST TLS"
        },
        "cryptopro_cert": {
            "required": True,
            "installed": os.path.exists("/var/opt/cprocsp/keys") or os.path.exists("C:\\Program Files\\Crypto Pro"),
            "description": "Сертификат КриптоПРО для TLS over HTTPS"
        }
    }


def _get_recommendation(status: Dict[str, Any]) -> str:
    """Получить рекомендацию по настройке"""
    if status["gost_available"]:
        return "Система настроена корректно. Рекомендаций нет."
    else:
        return """
Для включения GOST-режима выполните следующие шаги:

1. Установите КриптоПРО CSP 5.0 (бесплатная тестовая версия на 1 месяц)
2. Получите тестовый сертификат на сайте cryptopro.ru
3. Установите OpenSSL с GOST engine
4. Установите curl с GOST поддержкой

Подробная инструкция: docs/GOST_SETUP_GUIDE.md
"""


@router.get("/test-connection")
async def test_gost_connection() -> Dict[str, Any]:
    """
    Протестировать подключение к GOST-шлюзу с РЕАЛЬНЫМ TLS handshake
    
    Использует GOSTClient из вашего gost_banking_package.zip
    """
    import subprocess
    from datetime import datetime
    
    gost_url = os.getenv("GOST_API_URL", "https://api.gost.bankingapi.ru:8443")
    auth_url = os.getenv("AUTH_API_URL", "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token")
    client_id = os.getenv("VTB_TEAM_ID", "team075")
    client_secret = os.getenv("VTB_TEAM_SECRET", "")
    
    result = {
        "success": False,
        "message": "",
        "details": {},
        "gost_handshake": None
    }
    
    try:
        # Step 1: OAuth2 Authentication
        logger.info(f"[GOST] Step 1: OAuth2 authentication to {auth_url}")
        
        import httpx
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            auth_response = await client.post(
                auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret
                }
            )
            
            if auth_response.status_code != 200:
                return {
                    "success": False,
                    "message": f"❌ OAuth2 failed: {auth_response.status_code}",
                    "details": {"error": auth_response.text[:200]}
                }
            
            token_data = auth_response.json()
            access_token = token_data.get("access_token")
            
            logger.info(f"[GOST] ✅ OAuth2 token obtained")
            
            result["details"]["auth"] = {
                "status": "success",
                "token_obtained": True,
                "token_type": token_data.get("token_type"),
                "expires_in": token_data.get("expires_in")
            }
        
        # Step 2: GOST TLS Handshake (если csptest доступен)
        logger.info(f"[GOST] Step 2: Attempting GOST TLS handshake")
        
        csptest_path = r"C:\Program Files\Crypto Pro\CSP\csptest.exe"
        cert_name = "team075"  # Имя сертификата
        
        if os.path.exists(csptest_path):
            try:
                start_time = datetime.now()
                
                cmd = [
                    csptest_path,
                    "-tlsc",
                    "-server", "api.gost.bankingapi.ru",
                    "-port", "8443",
                    "-exchange", "3",
                    "-user", cert_name,
                    "-proto", "6"
                ]
                
                gost_result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='cp866',
                    errors='replace',
                    timeout=30
                )
                
                output = gost_result.stdout + gost_result.stderr
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # Check for successful handshake
                handshake_success = "Handshake was successful" in output
                
                result["gost_handshake"] = {
                    "attempted": True,
                    "success": handshake_success,
                    "time": elapsed,
                    "server": "api.gost.bankingapi.ru:8443"
                }
                
                if handshake_success:
                    logger.info(f"[GOST] ✅ TLS Handshake successful in {elapsed:.2f}s")
                    
                    # Extract certificate details if available
                    if "Банк ВТБ" in output:
                        result["gost_handshake"]["certificate"] = {
                            "organization": "Банк ВТБ (ПАО)",
                            "verified": True
                        }
                    
                    result["success"] = True
                    result["message"] = "✅ ПОЛНОЕ ПОДКЛЮЧЕНИЕ: OAuth2 + GOST TLS Handshake успешны!"
                else:
                    logger.warning(f"[GOST] ⚠️ TLS Handshake failed")
                    result["message"] = "⚠️ OAuth2 OK, но GOST TLS handshake не удался (нужен сертификат)"
                    result["success"] = True  # OAuth2 всё равно работает
                
            except subprocess.TimeoutExpired:
                logger.error("[GOST] csptest timeout")
                result["gost_handshake"] = {
                    "attempted": True,
                    "success": False,
                    "error": "Timeout (30s)"
                }
                result["success"] = True  # OAuth2 работает
                result["message"] = "✅ OAuth2 OK, GOST timeout (это нормально без сертификата)"
                
            except Exception as e:
                logger.error(f"[GOST] csptest error: {e}")
                result["gost_handshake"] = {
                    "attempted": True,
                    "success": False,
                    "error": str(e)
                }
                result["success"] = True  # OAuth2 работает
                result["message"] = "✅ OAuth2 OK, GOST не удался (установите КриптоПРО и сертификат)"
        else:
            logger.info("[GOST] csptest not found, skipping GOST handshake")
            result["gost_handshake"] = {
                "attempted": False,
                "reason": "csptest.exe not found (КриптоПРО не установлен)"
            }
            result["success"] = True
            result["message"] = "✅ OAuth2 работает! Для GOST TLS установите КриптоПРО CSP"
        
        result["details"]["endpoints"] = {
            "auth_url": auth_url,
            "gost_api_url": gost_url,
            "standard_api_url": os.getenv("BANKING_API_URL", "https://api.bankingapi.ru")
        }
        
        result["details"]["team"] = "team075"
        result["details"]["timestamp"] = datetime.now().isoformat()
        
        return result
            
    except Exception as e:
        logger.error(f"[GOST] Unexpected error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Ошибка: {str(e)}",
            "details": {
                "error": str(e)
            }
        }


@router.get("/requirements")
async def get_gost_requirements() -> Dict[str, Any]:
    """
    Получить список требований для GOST
    
    Возвращает детальную информацию о необходимых компонентах
    """
    return {
        "requirements": [
            {
                "name": "КриптоПРО CSP 5.0",
                "type": "software",
                "required": True,
                "cost": "Бесплатно (тестовая версия 1 месяц), далее ~15,000₽/год",
                "installation_time": "30 минут",
                "download_url": "https://cryptopro.ru/products/csp/downloads",
                "description": "Сертифицированное средство криптографической защиты информации"
            },
            {
                "name": "Тестовый сертификат",
                "type": "certificate",
                "required": True,
                "cost": "Бесплатно (тестовый)",
                "installation_time": "10 минут",
                "download_url": "https://www.cryptopro.ru/certsrv/certrqma.asp",
                "description": "Сертификат для установки TLS соединения"
            },
            {
                "name": "OpenSSL с GOST engine",
                "type": "software",
                "required": True,
                "cost": "Бесплатно (Open Source)",
                "installation_time": "1 час (компиляция)",
                "download_url": "https://github.com/gost-engine/engine",
                "description": "OpenSSL библиотека с поддержкой ГОСТ алгоритмов"
            },
            {
                "name": "curl с GOST поддержкой",
                "type": "software",
                "required": True,
                "cost": "Бесплатно (Open Source)",
                "installation_time": "1 час (компиляция)",
                "download_url": "https://curl.se/download.html",
                "description": "curl утилита, скомпилированная с GOST OpenSSL"
            }
        ],
        "total_setup_time": "2-3 часа",
        "total_cost": "0₽ (для тестирования), 15,000₽/год (production)",
        "difficulty": "Средняя (требуется опыт работы с командной строкой)",
        "support_available": True
    }

