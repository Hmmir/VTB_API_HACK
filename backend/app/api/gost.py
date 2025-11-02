"""
GOST Status API
Endpoint для проверки статуса GOST-поддержки
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import os

from app.database import get_db
from app.services.gost_adapter import GOSTAdapter, GOSTMode

router = APIRouter(prefix="/gost", tags=["GOST"])


@router.get("/status")
async def get_gost_status() -> Dict[str, Any]:
    """
    Получить статус GOST-поддержки
    
    Возвращает информацию о доступности GOST-шлюза и текущем режиме работы
    """
    # Создаем временный адаптер для проверки
    adapter = GOSTAdapter(
        client_id=os.getenv("VTB_CLIENT_ID", "team075"),
        client_secret=os.getenv("VTB_CLIENT_SECRET", ""),
        mode=GOSTMode.AUTO
    )
    
    try:
        status = adapter.get_status()
        
        # Добавляем человекочитаемые описания
        return {
            "enabled": status["gost_available"],
            "mode": status["gost_mode"],
            "api_endpoint": status["current_api"],
            "description": _get_status_description(status),
            "requirements": _get_requirements_status(),
            "recommendation": _get_recommendation(status)
        }
    finally:
        await adapter.close()


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
    Протестировать подключение к GOST-шлюзу
    
    Попытка выполнить реальный запрос к GOST API
    """
    adapter = GOSTAdapter(
        client_id=os.getenv("VTB_CLIENT_ID", "team075"),
        client_secret=os.getenv("VTB_CLIENT_SECRET", ""),
        mode=GOSTMode.GOST  # Принудительно используем GOST
    )
    
    try:
        # Пытаемся получить токен
        token = await adapter.get_access_token()
        
        # Пытаемся выполнить простой запрос
        # (если API требует конкретный endpoint, замените на него)
        try:
            # Пример запроса к API
            result = await adapter.get("/api/rb/accounts/v1/accounts")
            
            return {
                "success": True,
                "message": "✅ GOST-шлюз работает корректно",
                "details": {
                    "token_obtained": True,
                    "api_accessible": True,
                    "endpoint": adapter._get_api_base()
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"⚠️ Токен получен, но API недоступен: {str(e)}",
                "details": {
                    "token_obtained": True,
                    "api_accessible": False,
                    "error": str(e)
                }
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Не удалось подключиться к GOST-шлюзу: {str(e)}",
            "details": {
                "token_obtained": False,
                "error": str(e)
            }
        }
    finally:
        await adapter.close()


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

