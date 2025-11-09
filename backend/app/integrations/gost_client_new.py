"""
GOST Banking Client - Готовая библиотека для работы с Open Banking API через GOST TLS

Использование:
    from lib.gost_client import GOSTClient
    
    client = GOSTClient(
        client_id="your_id",
        client_secret="your_secret",
        cert_name="Your Certificate"
    )
    
    # Проверка GOST
    if client.test_gost():
        print("GOST работает!")
    
    # Получение данных
    accounts = client.get_accounts()
"""

import subprocess
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GOSTClient:
    """Клиент для работы с Open Banking API через GOST TLS"""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        cert_name: str,
        auth_url: str = "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token",
        api_url: str = "https://api.bankingapi.ru",
        gost_url: str = "https://api.gost.bankingapi.ru:8443",
        csptest_path: str = r"C:\Program Files\Crypto Pro\CSP\csptest.exe"
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.cert_name = cert_name
        self.auth_url = auth_url
        self.api_url = api_url
        self.gost_url = gost_url
        self.csptest_path = csptest_path
        
        self.token = None
        self.token_expires_at = None
        
        logger.info(f"Инициализирован GOST Client для {client_id}")
    
    def authenticate(self) -> str:
        """Получить access token"""
        logger.info("Получение access token...")
        
        try:
            response = requests.post(
                self.auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            self.token = data["access_token"]
            expires_in = data.get("expires_in", 300)
            self.token_expires_at = datetime.now().timestamp() + expires_in
            
            logger.info(f"✅ Token получен, действителен {expires_in} секунд")
            return self.token
            
        except Exception as e:
            logger.error(f"❌ Ошибка аутентификации: {e}")
            raise
    
    def _ensure_token(self):
        """Проверить и обновить токен если нужно"""
        if not self.token or (
            self.token_expires_at and 
            datetime.now().timestamp() >= self.token_expires_at - 30
        ):
            self.authenticate()
    
    def test_gost(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Проверить GOST TLS подключение
        
        Returns:
            {
                "success": bool,
                "cipher": str,
                "server": str,
                "time": float
            }
        """
        logger.info("Тест GOST TLS...")
        start_time = datetime.now()
        
        try:
            cmd = [
                self.csptest_path,
                "-tlsc",
                "-server", "api.gost.bankingapi.ru",
                "-port", "8443",
                "-exchange", "3",
                "-user", self.cert_name,
                "-proto", "6",
                "-verbose"  # Всегда используем verbose для получения полной информации
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp866',
                errors='replace',
                timeout=30
            )
            
            output = result.stdout + result.stderr
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # Для отладки: вывести результат
            if verbose:
                logger.debug(f"csptest output:\n{output}")
            
            # Success определяется по handshake, даже если проверка сертификата не прошла
            success = "Handshake was successful" in output
            
            # Извлечь cipher
            cipher = None
            for line in output.split('\n'):
                if "TLS_GOSTR" in line and "CipherSuite" in line:
                    if "TLS_GOSTR341112_256_WITH_KUZNYECHIK" in line:
                        cipher = "TLS_GOSTR341112_256_WITH_KUZNYECHIK_CTR_OMAC"
                    break
            
            # Извлечь сервер
            server = None
            if "Банк ВТБ" in output:
                server = "Банк ВТБ (ПАО)"
            
            result_dict = {
                "success": success,
                "cipher": cipher,
                "server": server,
                "time": elapsed
            }
            
            if success:
                logger.info(f"✅ GOST TLS работает! ({elapsed:.2f}s)")
            else:
                logger.error("❌ GOST TLS не работает")
            
            return result_dict
            
        except Exception as e:
            logger.error(f"❌ Ошибка GOST: {e}")
            return {"success": False, "error": str(e)}
    
    def call_api(
        self,
        endpoint: str,
        method: str = "GET",
        use_gost: bool = False,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Вызвать API endpoint"""
        self._ensure_token()
        
        base_url = self.gost_url if use_gost else self.api_url
        url = f"{base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"{method} {url} (GOST: {use_gost})")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            logger.info(f"Response: {response.status_code}")
            
            if response.status_code == 401:
                logger.warning("401, обновляем токен...")
                self.authenticate()
                headers["Authorization"] = f"Bearer {self.token}"
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    timeout=10
                )
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            else:
                return {"status": "success", "code": response.status_code}
                
        except Exception as e:
            logger.error(f"❌ Ошибка API: {e}")
            raise
    
    # Удобные методы
    
    def get_accounts(self, use_gost: bool = False):
        """Получить список счетов"""
        return self.call_api("/api/rb/accounts/v1/accounts", use_gost=use_gost)
    
    def get_transactions(self, account_id: str, use_gost: bool = False):
        """Получить транзакции по счёту"""
        return self.call_api(
            f"/api/rb/transactions/v1/accounts/{account_id}/transactions",
            use_gost=use_gost
        )
    
    def get_cards(self, use_gost: bool = False):
        """Получить список карт"""
        return self.call_api("/api/rb/cards/v1/cards", use_gost=use_gost)
    
    def health_check(self) -> Dict[str, bool]:
        """Проверка всех компонентов"""
        logger.info("Health check...")
        
        results = {
            "auth": False,
            "standard_api": False,
            "gost_tls": False
        }
        
        # Auth
        try:
            self.authenticate()
            results["auth"] = True
        except:
            pass
        
        # Standard API
        try:
            self.call_api("/api/rb/accounts/v1/accounts", use_gost=False)
            results["standard_api"] = True
        except:
            pass
        
        # GOST TLS
        gost_result = self.test_gost()
        results["gost_tls"] = gost_result["success"]
        
        return results

