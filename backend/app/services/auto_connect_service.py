"""Auto-connect service for team075-X users."""
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.openbanking_service import OpenBankingService


class AutoConnectService:
    """Service to automatically connect team075-X users to their banks."""
    
    @staticmethod
    async def auto_connect_team_client(db: Session, user: User):
        """Automatically connect all 3 banks for team075-X user.
        
        When a user registers/logs in as team075-1, team075-2, etc.,
        automatically connect their accounts from all 3 banks.
        
        Args:
            db: Database session
            user: User object (must be team075-X format)
        """
        # Check if user is team075-X format
        if not user.email.startswith("team075-"):
            return
        
        # Skip if already has connections
        from app.models.bank_connection import BankConnection
        existing_connections = db.query(BankConnection).filter(
            BankConnection.user_id == user.id
        ).count()
        
        if existing_connections > 0:
            return
        
        # Auto-connect all 3 banks
        banks = ["vbank", "abank", "sbank"]
        
        for bank_code in banks:
            try:
                await OpenBankingService.connect_bank_with_team_client(
                    db,
                    user,
                    bank_code,
                    client_number="1"  # Will use user's own team075-X
                )
                print(f"✅ Auto-connected {bank_code} for {user.email}")
            except Exception as e:
                print(f"❌ Failed to auto-connect {bank_code} for {user.email}: {e}")
                # Continue with other banks even if one fails
                continue


