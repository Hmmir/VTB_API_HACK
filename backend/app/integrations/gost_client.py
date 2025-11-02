"""
GOST API Client - использует curl с GOST поддержкой через subprocess
"""
import subprocess
import json
import os
import tempfile
from typing import Optional, Dict, Any


class GOSTClient:
    """
    Клиент для работы с GOST API через curl
    Требует установленный curl с GOST поддержкой
    """
    
    def __init__(self, team_id: str, team_secret: str, cert_container: str = "VTB_Test_Container"):
        self.team_id = team_id
        self.team_secret = team_secret
        self.cert_container = cert_container
        self.base_url = "https://api.gost.bankingapi.ru:8443"
        self.auth_url = "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token"
        self._access_token: Optional[str] = None
    
    def _find_curl(self) -> Optional[str]:
        """Ищет curl с GOST поддержкой"""
        # Вариант 1: Стандартный curl (может не работать)
        curl_paths = [
            "curl",
            r"C:\Windows\System32\curl.exe",
            r"C:\Program Files\Git\usr\bin\curl.exe",
        ]
        
        for path in curl_paths:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Проверяем поддержку GOST (в выводе должно быть что-то про GOST)
                    if "gost" in result.stdout.lower() or "GOST" in result.stdout:
                        return path
                    # Иначе пробуем использовать стандартный curl
                    return path
            except Exception:
                continue
        
        return None
    
    def get_access_token(self) -> str:
        """Получает access token для аутентификации"""
        if self._access_token:
            return self._access_token
        
        curl_path = self._find_curl()
        if not curl_path:
            raise RuntimeError("curl не найден. Установите curl с GOST поддержкой.")
        
        # Формируем curl команду для получения токена
        cmd = [
            curl_path,
            "-v",
            "--data", f"grant_type=client_credentials&client_id={self.team_id}&client_secret={self.team_secret}",
            "-H", "Content-Type: application/x-www-form-urlencoded",
            self.auth_url
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Ошибка получения токена: {result.stderr}")
            
            # Парсим JSON ответ
            response_text = result.stdout
            # Убираем заголовки curl из вывода
            json_start = response_text.find("{")
            if json_start == -1:
                raise RuntimeError(f"Не найден JSON в ответе: {response_text}")
            
            token_data = json.loads(response_text[json_start:])
            self._access_token = token_data.get("access_token")
            
            if not self._access_token:
                raise RuntimeError(f"Токен не найден в ответе: {token_data}")
            
            return self._access_token
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Таймаут при получении токена")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Ошибка парсинга JSON: {e}")
    
    def request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Выполняет запрос к GOST API
        
        Args:
            endpoint: Путь API (например, "/api/rb/rewardsPay/hackathon/v1/...")
            method: HTTP метод (GET, POST, etc.)
            data: Данные для POST запроса
        
        Returns:
            Ответ API в виде словаря
        """
        curl_path = self._find_curl()
        if not curl_path:
            raise RuntimeError("curl не найден. Установите curl с GOST поддержкой.")
        
        token = self.get_access_token()
        url = f"{self.base_url}{endpoint}"
        
        # Формируем curl команду
        cmd = [
            curl_path,
            "-v",
            "-X", method,
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
        ]
        
        # Добавляем сертификат (если указан)
        if self.cert_container:
            # Windows: --cert использует имя контейнера
            # Linux: --cert использует путь к файлу
            cmd.extend(["--cert", self.cert_container])
        
        # Добавляем данные для POST/PUT
        if data and method in ["POST", "PUT", "PATCH"]:
            # Сохраняем данные во временный файл
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(data, f)
                temp_file = f.name
            
            cmd.extend(["--data", f"@{temp_file}"])
        
        cmd.append(url)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Удаляем временный файл
            if data and method in ["POST", "PUT", "PATCH"]:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            if result.returncode != 0:
                raise RuntimeError(f"Ошибка запроса: {result.stderr}")
            
            # Парсим JSON ответ
            response_text = result.stdout
            json_start = response_text.find("{")
            if json_start == -1:
                # Возможно, ответ не JSON
                return {"raw_response": response_text}
            
            return json.loads(response_text[json_start:])
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Таймаут при выполнении запроса")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Ошибка парсинга JSON: {e}")

