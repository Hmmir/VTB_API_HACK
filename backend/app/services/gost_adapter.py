"""
GOST TLS Adapter для работы с VTB Open Banking API
Поддерживает два режима:
1. GOST-шлюз (api.gost.bankingapi.ru:8443)
2. Стандартный API (api.bankingapi.ru)
"""

import os
import httpx
import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class GOSTMode(str, Enum):
    """Режимы работы с API"""
    GOST = "gost"  # Через GOST-шлюз
    STANDARD = "standard"  # Стандартный API
    AUTO = "auto"  # Автоматический выбор


class GOSTAdapter:
    """
    Адаптер для работы с VTB Open Banking API с поддержкой GOST
    
    Автоматически определяет доступность GOST-шлюза и переключается
    на стандартный API если GOST недоступен.
    """
    
    # API endpoints
    GOST_API_BASE = "https://api.gost.bankingapi.ru:8443"
    STANDARD_API_BASE = "https://api.bankingapi.ru"
    AUTH_URL = "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        mode: GOSTMode = GOSTMode.AUTO,
        use_gost_curl: bool = False
    ):
        """
        Инициализация адаптера
        
        Args:
            client_id: Team ID (например, team075)
            client_secret: Team secret
            mode: Режим работы (GOST/STANDARD/AUTO)
            use_gost_curl: Использовать кастомный curl с GOST поддержкой
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.mode = mode
        self.use_gost_curl = use_gost_curl
        
        # Определяем текущий режим
        self._current_mode: Optional[GOSTMode] = None
        self._gost_available: Optional[bool] = None
        self._access_token: Optional[str] = None
        
        # Настройка httpx клиента
        self._init_http_client()
    
    def _init_http_client(self):
        """Инициализация HTTP клиента"""
        # Настройки для GOST
        if self.mode == GOSTMode.GOST or self.mode == GOSTMode.AUTO:
            # Проверяем наличие GOST-инструментов
            self._gost_available = self._check_gost_availability()
        
        # Создаем httpx клиент с нужными настройками
        self.client = httpx.AsyncClient(
            timeout=30.0,
            verify=True,  # Проверяем SSL сертификаты
            follow_redirects=True
        )
    
    def _check_gost_availability(self) -> bool:
        """
        Проверяет доступность GOST-инфраструктуры
        
        Проверяет:
        1. Наличие OpenSSL с GOST
        2. Наличие curl с GOST
        3. Наличие сертификата КриптоПРО
        """
        try:
            # TODO: Реализовать полную проверку
            # Пока возвращаем False, т.к. требуется настройка
            logger.info("Checking GOST availability...")
            
            # Проверяем переменные окружения
            has_gost_openssl = os.path.exists("/usr/local/bin/openssl-gost")
            has_gost_curl = os.path.exists("/usr/local/bin/curl-gost")
            has_cryptopro_cert = os.path.exists("/var/opt/cprocsp/keys")
            
            gost_ready = has_gost_openssl and has_gost_curl and has_cryptopro_cert
            
            if gost_ready:
                logger.info("✅ GOST infrastructure is available")
            else:
                logger.warning("⚠️ GOST infrastructure is not fully configured")
                logger.info(f"  - OpenSSL with GOST: {'✅' if has_gost_openssl else '❌'}")
                logger.info(f"  - curl with GOST: {'✅' if has_gost_curl else '❌'}")
                logger.info(f"  - КриптоПРО certificate: {'✅' if has_cryptopro_cert else '❌'}")
            
            return gost_ready
            
        except Exception as e:
            logger.warning(f"Failed to check GOST availability: {e}")
            return False
    
    async def get_access_token(self) -> str:
        """
        Получить access_token для работы с API
        
        Returns:
            Access token
        """
        if self._access_token:
            return self._access_token
        
        try:
            logger.info(f"Getting access token for {self.client_id}...")
            
            response = await self.client.post(
                self.AUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            self._access_token = data["access_token"]
            logger.info("✅ Successfully obtained access token")
            
            return self._access_token
            
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise
    
    def _get_api_base(self) -> str:
        """Получить базовый URL API в зависимости от режима"""
        if self.mode == GOSTMode.GOST:
            return self.GOST_API_BASE
        elif self.mode == GOSTMode.STANDARD:
            return self.STANDARD_API_BASE
        else:  # AUTO
            if self._gost_available:
                logger.info("Using GOST API endpoint")
                return self.GOST_API_BASE
            else:
                logger.info("Using standard API endpoint (GOST not available)")
                return self.STANDARD_API_BASE
    
    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Выполнить запрос к API
        
        Args:
            method: HTTP метод (GET, POST, etc.)
            endpoint: API endpoint (например, /api/rb/accounts/v1/accounts)
            **kwargs: Дополнительные параметры для httpx
        
        Returns:
            JSON response
        """
        # Получаем токен если нужно
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        
        if "Authorization" not in kwargs["headers"]:
            token = await self.get_access_token()
            kwargs["headers"]["Authorization"] = f"Bearer {token}"
        
        # Формируем полный URL
        base_url = self._get_api_base()
        url = f"{base_url}{endpoint}"
        
        try:
            logger.info(f"{method} {url}")
            
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            
            # Если GOST недоступен, пробуем стандартный API
            if self.mode == GOSTMode.AUTO and base_url == self.GOST_API_BASE:
                logger.warning("GOST API failed, falling back to standard API...")
                self._gost_available = False
                return await self.request(method, endpoint, **kwargs)
            
            raise
        
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET запрос"""
        return await self.request("GET", endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """POST запрос"""
        return await self.request("POST", endpoint, **kwargs)
    
    async def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """PUT запрос"""
        return await self.request("PUT", endpoint, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE запрос"""
        return await self.request("DELETE", endpoint, **kwargs)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получить статус GOST-поддержки
        
        Returns:
            Словарь со статусом
        """
        return {
            "gost_mode": self.mode.value,
            "gost_available": self._gost_available or False,
            "current_api": self._get_api_base(),
            "has_token": self._access_token is not None
        }
    
    async def close(self):
        """Закрыть соединения"""
        await self.client.aclose()


# Пример использования
async def main():
    """Пример использования GOST адаптера"""
    
    # Создаем адаптер (AUTO режим - автоматически выберет GOST или стандартный API)
    adapter = GOSTAdapter(
        client_id="team075",
        client_secret=os.getenv("VTB_CLIENT_SECRET"),
        mode=GOSTMode.AUTO
    )
    
    try:
        # Проверяем статус
        status = adapter.get_status()
        print("GOST Status:", status)
        
        # Пример: получение списка счетов
        # accounts = await adapter.get("/api/rb/accounts/v1/accounts")
        # print("Accounts:", accounts)
        
    finally:
        await adapter.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

