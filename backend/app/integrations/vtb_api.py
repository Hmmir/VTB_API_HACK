"""OpenBanking Russia Sandbox API client."""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings


class OpenBankingClient:
    """Client for OpenBanking Russia Sandbox API with GOST support."""
    
    # Bank base URLs (from https://vbank.open.bankingapi.ru/docs)
    BANK_URLS = {
        "vbank": "https://vbank.open.bankingapi.ru",
        "abank": "https://abank.open.bankingapi.ru",
        "sbank": "https://sbank.open.bankingapi.ru",
    }
    
    def __init__(self, bank_code: str = "vbank", use_gost: Optional[bool] = None):
        """Initialize client for specific bank.
        
        Args:
            bank_code: Bank code (vbank, abank, sbank)
            use_gost: Override GOST setting
        """
        self.bank_code = bank_code
        self.use_gost = use_gost if use_gost is not None else False
        
        # Choose base URL based on GOST setting
        if self.use_gost:
            # GOST Gateway - all banks through unified gateway
            self.base_url = settings.GOST_API_BASE
            print(f"🔒 Using GOST Gateway: {self.base_url}")
        else:
            # Standard connection - direct to specific bank
            # Each bank has its own URL: vbank.open.bankingapi.ru, abank.open.bankingapi.ru, etc.
            self.base_url = self.BANK_URLS.get(bank_code, self.BANK_URLS["vbank"])
            print(f"🌐 Using {bank_code} API: {self.base_url}")
        
        self.team_id = settings.VTB_TEAM_ID
        
        # Configure httpx client
        client_kwargs = {"timeout": 30.0}
        
        if self.use_gost:
            # For GOST, disable SSL verification (use proper certs in production)
            client_kwargs["verify"] = False
            print("⚠️  GOST mode: SSL verification disabled")
        
        self.client = httpx.AsyncClient(**client_kwargs)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _get_headers(
        self, 
        access_token: Optional[str] = None,
        consent_id: Optional[str] = None,
        requesting_bank: Optional[str] = None
    ) -> Dict[str, str]:
        """Get request headers for OpenBanking API.
        
        Args:
            access_token: Bearer token
            consent_id: Consent ID for inter-bank requests
            requesting_bank: Bank code making the request (for inter-bank)
        """
        headers = {
            "Content-Type": "application/json",
        }
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        # For inter-bank requests
        if consent_id:
            headers["X-Consent-Id"] = consent_id
        if requesting_bank:
            headers["X-Requesting-Bank"] = requesting_bank
        
        return headers
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_bank_token(self) -> Dict[str, Any]:
        """Get bank token for API access.
        
        This is the main auth method for OpenBanking Russia Sandbox.
        Returns token valid for 24 hours.
        For sandbox, use demo client_id/secret.
        
        Returns:
            Dict with access_token and expires_in
        """
        url = f"{self.base_url}/auth/bank-token"
        
        # For sandbox, use demo credentials
        params = {
            "client_id": self.team_id or "demo",
            "client_secret": "secret"
        }
        
        response = await self.client.post(
            url,
            params=params,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_random_demo_client(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Get random demo client credentials for testing.
        
        Args:
            access_token: Bank token (optional for sandbox)
            
        Returns:
            Dict with client credentials (person_id, full_name, password)
        """
        url = f"{self.base_url}/auth/random-demo-client"
        
        headers = self._get_headers(access_token) if access_token else {}
        response = await self.client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def client_login(
        self,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """Login as a bank client.
        
        Args:
            username: Client username
            password: Client password
            
        Returns:
            Dict with client_token (valid 24h)
        """
        url = f"{self.base_url}/auth/login"
        data = {
            "username": username,
            "password": password
        }
        
        response = await self.client.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    # === Consents API ===
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def request_consent(
        self,
        client_token: str,
        consent_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request account access consent.
        
        Required for inter-bank requests.
        
        Args:
            client_token: Client token
            consent_data: Consent parameters
            
        Returns:
            Dict with consent_id and status
        """
        url = f"{self.base_url}/account-consents/request"
        
        response = await self.client.post(
            url,
            json=consent_data,
            headers=self._get_headers(client_token)
        )
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_consent(
        self,
        client_token: str,
        consent_id: str
    ) -> Dict[str, Any]:
        """Get consent details."""
        url = f"{self.base_url}/account-consents/{consent_id}"
        
        response = await self.client.get(
            url,
            headers=self._get_headers(client_token)
        )
        response.raise_for_status()
        return response.json()
    
    # === Accounts API ===
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_accounts(
        self,
        client_token: str,
        consent_id: Optional[str] = None,
        requesting_bank: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get client accounts.
        
        Own bank: только client_token
        Other bank: требуется consent_id и requesting_bank
        
        Args:
            client_token: Client authentication token
            consent_id: Consent ID (for inter-bank)
            requesting_bank: Requesting bank code (for inter-bank)
        """
        url = f"{self.base_url}/accounts"
        
        response = await self.client.get(
            url,
            headers=self._get_headers(client_token, consent_id, requesting_bank)
        )
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_account(
        self,
        client_token: str,
        account_id: str,
        consent_id: Optional[str] = None,
        requesting_bank: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get specific account details."""
        url = f"{self.base_url}/accounts/{account_id}"
        
        response = await self.client.get(
            url,
            headers=self._get_headers(client_token, consent_id, requesting_bank)
        )
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_balances(
        self,
        client_token: str,
        account_id: str,
        consent_id: Optional[str] = None,
        requesting_bank: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get account balances."""
        url = f"{self.base_url}/accounts/{account_id}/balances"
        
        response = await self.client.get(
            url,
            headers=self._get_headers(client_token, consent_id, requesting_bank)
        )
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_transactions(
        self,
        client_token: str,
        account_id: str,
        consent_id: Optional[str] = None,
        requesting_bank: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get account transactions."""
        url = f"{self.base_url}/accounts/{account_id}/transactions"
        
        params = {}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        
        response = await self.client.get(
            url,
            headers=self._get_headers(client_token, consent_id, requesting_bank),
            params=params if params else None
        )
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def create_account(
        self,
        client_token: str,
        account_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create new account."""
        url = f"{self.base_url}/accounts"
        
        response = await self.client.post(
            url,
            json=account_data,
            headers=self._get_headers(client_token)
        )
        response.raise_for_status()
        return response.json()
    
    # === Products API ===
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_products(
        self,
        access_token: Optional[str] = None,
        product_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get bank products catalog (public endpoint, no auth required).
        
        Args:
            access_token: Optional access token (not needed for public products)
            product_type: Filter by type (deposit, loan, credit_card, etc.)
        """
        url = f"{self.base_url}/products"
        
        params = {}
        if product_type:
            params["product_type"] = product_type
        
        # Products are public - no auth headers needed
        response = await self.client.get(
            url,
            params=params if params else None
        )
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_product(
        self,
        bank_token: str,
        product_id: str
    ) -> Dict[str, Any]:
        """Get specific product details."""
        url = f"{self.base_url}/products/{product_id}"
        
        response = await self.client.get(
            url,
            headers=self._get_headers(bank_token)
        )
        response.raise_for_status()
        return response.json()
    
    # === Payments API ===
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def create_payment(
        self,
        client_token: str,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create payment."""
        url = f"{self.base_url}/payments"
        
        response = await self.client.post(
            url,
            json=payment_data,
            headers=self._get_headers(client_token)
        )
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_payment(
        self,
        client_token: str,
        payment_id: str
    ) -> Dict[str, Any]:
        """Get payment status."""
        url = f"{self.base_url}/payments/{payment_id}"
        
        response = await self.client.get(
            url,
            headers=self._get_headers(client_token)
        )
        response.raise_for_status()
        return response.json()
    
    # === Product Agreements API ===
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_agreements(
        self,
        client_token: str
    ) -> List[Dict[str, Any]]:
        """Get client's product agreements (deposits, loans, cards)."""
        url = f"{self.base_url}/product-agreements"
        
        response = await self.client.get(
            url,
            headers=self._get_headers(client_token)
        )
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def create_agreement(
        self,
        client_token: str,
        agreement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Open new product agreement."""
        url = f"{self.base_url}/product-agreements"
        
        response = await self.client.post(
            url,
            json=agreement_data,
            headers=self._get_headers(client_token)
        )
        response.raise_for_status()
        return response.json()


# Backward compatibility alias
VTBAPIClient = OpenBankingClient

