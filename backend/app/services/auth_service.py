"""Authentication service."""
from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.integrations.mybank_client import get_mybank_client, DEFAULT_MYBANK_PASSWORD
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """Register a new user."""
        # Normalize email: add @financehub.ru if not present
        email = user_data.email
        if '@' not in email:
            email = f"{email}@financehub.ru"
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_pwd = hash_password(user_data.password)
        
        # ГОСТ режим ТОЛЬКО для team075-demo (специальный демо-пользователь)
        # Обычные team075-X клиенты работают через 3 банка (sandbox)
        use_gost = email == "team075-demo@financehub.ru"
        
        new_user = User(
            email=email,  # Use normalized email
            hashed_password=hashed_pwd,
            full_name=user_data.full_name,
            phone=user_data.phone,
            use_gost_mode=use_gost
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Автоматически создаем аккаунт в MyBank для целей и семейных счетов
        loop = None
        try:
            mybank = get_mybank_client()
            
            async def register_mybank():
                try:
                    await mybank.register_customer(
                        full_name=user_data.full_name or email.split('@')[0],
                        email=email,
                        phone=user_data.phone or "+70000000000",
                        password=DEFAULT_MYBANK_PASSWORD
                    )
                    logger.info(f"✅ MyBank account created for {email}")
                except httpx.HTTPStatusError as http_err:
                    if http_err.response.status_code == 400:
                        logger.info(f"ℹ️ MyBank account already exists for {email}")
                    else:
                        raise
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(register_mybank())
        except Exception as e:
            logger.warning(f"⚠️ Failed to create MyBank account for {email}: {e}")
        finally:
            try:
                if loop:
                    loop.close()
            except Exception:
                pass
        
        return new_user
    
    @staticmethod
    async def login_user(db: Session, credentials: UserLogin) -> Token:
        """Login user and return tokens."""
        # Normalize email: add @financehub.ru if not present
        email = credentials.email
        if '@' not in email:
            email = f"{email}@financehub.ru"
        
        # Find user
        user = db.query(User).filter(User.email == email).first()
        
        # Auto-register team075-X users if they don't exist
        if not user and email.startswith("team075-") and email.endswith("@financehub.ru"):
            from app.schemas.user import UserCreate
            try:
                user_data = UserCreate(
                    email=email,
                    password=credentials.password,
                    full_name=f"Team Client {email.split('@')[0]}"
                )
                user = AuthService.register_user(db, user_data)
            except Exception as e:
                print(f"⚠️ Auto-registration failed for {email}: {e}")
        
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Auto-connect banks for team075-X users and demo user
        if (user.email.startswith("team075-") and not user.email.endswith("-demo@financehub.ru")) or user.email == "demo@financehub.ru":
            from app.services.auto_connect_service import AutoConnectService
            try:
                await AutoConnectService.auto_connect_team_client(db, user)
            except Exception as e:
                print(f"⚠️ Auto-connect failed for {user.email}: {e}")
                # Don't fail login if auto-connect fails
        
        # Create tokens
        token_data = {"user_id": user.id, "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new tokens
        token_data = {
            "user_id": payload["user_id"],
            "email": payload["email"]
        }
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token
        )
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """Get current user from access token."""
        payload = decode_token(token)
        
        if not payload or payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token"
            )
        
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user

