"""
MyBank API Client
Интеграция с собственным банком-sandbox для создания карт, счетов и целей
"""
import httpx
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import logging

from app.config import settings, DEFAULT_MYBANK_PASSWORD as CONFIG_DEFAULT_MYBANK_PASSWORD

logger = logging.getLogger(__name__)

DEFAULT_MYBANK_PASSWORD = CONFIG_DEFAULT_MYBANK_PASSWORD


class MyBankClient:
    """Client for MyBank API integration"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.MYBANK_API_BASE_URL
        self.token: Optional[str] = None
        
    async def register_customer(
        self,
        full_name: str,
        email: str,
        phone: str,
        password: str
    ) -> Dict:
        """Register new customer in MyBank"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/register",
                json={
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "password": password
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def login(self, email: str, password: str) -> str:
        """Login and get access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/token",
                data={
                    "username": email,
                    "password": password
                }
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            return self.token
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if not self.token:
            raise ValueError("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self.token}"}
    
    async def get_customer_info(self) -> Dict:
        """Get current customer information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/customers/me",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def create_card(
        self,
        card_type: str = "debit",
        credit_limit: Optional[Decimal] = None
    ) -> Dict:
        """Issue new card"""
        async with httpx.AsyncClient() as client:
            payload = {"card_type": card_type}
            if credit_limit:
                payload["credit_limit"] = float(credit_limit)
                
            response = await client.post(
                f"{self.base_url}/customers/me/cards",
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def get_cards(self) -> List[Dict]:
        """Get customer's cards"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/customers/me/cards",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def create_account(
        self,
        account_type: str = "checking",
        linked_goal_id: Optional[str] = None
    ) -> Dict:
        """Create new account"""
        async with httpx.AsyncClient() as client:
            payload = {"account_type": account_type}
            if linked_goal_id:
                payload["linked_goal_id"] = linked_goal_id
                
            response = await client.post(
                f"{self.base_url}/customers/me/accounts",
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def get_accounts(self) -> List[Dict]:
        """Get customer's accounts"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/customers/me/accounts",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def transfer(
        self,
        from_account_id: str,
        to_account_id: str,
        amount: Decimal,
        description: str = "Transfer"
    ) -> Dict:
        """Transfer money between accounts"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/transfers",
                json={
                    "from_account_id": from_account_id,
                    "to_account_id": to_account_id,
                    "amount": float(amount),
                    "description": description
                },
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def create_goal(
        self,
        name: str,
        target_amount: Decimal,
        deadline: Optional[datetime] = None
    ) -> Dict:
        """Create savings goal with dedicated account"""
        async with httpx.AsyncClient() as client:
            payload = {
                "name": name,
                "target_amount": float(target_amount)
            }
            if deadline:
                payload["deadline"] = deadline.isoformat()
                
            response = await client.post(
                f"{self.base_url}/customers/me/goals",
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def get_goals(self) -> List[Dict]:
        """Get customer's goals"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/customers/me/goals",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def contribute_to_goal(
        self,
        goal_id: str,
        amount: Decimal,
        from_card_id: Optional[str] = None
    ) -> Dict:
        """Contribute to goal"""
        async with httpx.AsyncClient() as client:
            payload = {"amount": float(amount)}
            if from_card_id:
                payload["from_card_id"] = from_card_id
            
            logger.info(f"🔵 MyBank contribute_to_goal: goal_id={goal_id}, payload={payload}")
                
            response = await client.post(
                f"{self.base_url}/customers/me/goals/{goal_id}/contribute",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                logger.error(f"❌ MyBank contribute error: status={response.status_code}, body={response.text}")
            
            response.raise_for_status()
            return response.json()


# Singleton instance
_mybank_client = None

def get_mybank_client() -> MyBankClient:
    """Get or create MyBank client singleton"""
    global _mybank_client
    if _mybank_client is None:
        _mybank_client = MyBankClient()
    return _mybank_client


__all__ = ["MyBankClient", "get_mybank_client", "DEFAULT_MYBANK_PASSWORD"]
