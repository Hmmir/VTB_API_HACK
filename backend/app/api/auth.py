"""Authentication endpoints."""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.api.dependencies import get_current_user
from app.models.user import User
from app.utils.security import create_bank_token

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    user = AuthService.register_user(db, user_data)
    return user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and get access token."""
    return await AuthService.login_user(db, credentials)


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str):
    """Refresh access token."""
    return AuthService.refresh_access_token(refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


class BankTokenRequest(BaseModel):
    bank_code: str
    audience: str = "interbank"


class BankTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    algorithm: str = "RS256"
    expires_in: int = 3600


@router.post("/bank-token", response_model=BankTokenResponse)
def create_bank_token_endpoint(
    request: BankTokenRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate RS256 JWT token for interbank communication.
    
    This endpoint creates a bank-to-bank authentication token signed with RS256.
    The public key is available at /.well-known/jwks.json for verification.
    
    **Use cases:**
    - Interbank transfers
    - Consent-based account access
    - OpenBanking API authentication
    """
    try:
        token = create_bank_token(
            bank_code=request.bank_code,
            audience=request.audience
        )
        
        return BankTokenResponse(
            access_token=token,
            expires_in=3600
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

