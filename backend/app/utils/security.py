"""Security utilities: password hashing, JWT, encryption."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from app.config import settings

# Password hashing context (argon2 - modern, no length limits)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Encryption cipher  
def _get_encryption_key() -> bytes:
    """Get or generate encryption key."""
    # For development: always use a persistent key stored in container
    # In production, set ENCRYPTION_KEY environment variable
    import os
    key_file = "/tmp/fernet.key"
    
    # Check if we have a valid ENCRYPTION_KEY environment variable
    if settings.ENCRYPTION_KEY and settings.ENCRYPTION_KEY.strip():
        key_str = settings.ENCRYPTION_KEY.strip()
        # Check if it's valid base64 and correct length
        if len(key_str) == 44:
            try:
                key = key_str.encode()
                # Test that it works
                Fernet(key)
                return key
            except Exception as e:
                print(f"WARNING: Invalid ENCRYPTION_KEY: {e}")
                print(f"Falling back to file-based key")
    
    # Use file-based key for development
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        # Generate and persist new key
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        print(f"✅ Generated new encryption key and saved to {key_file}")
        print(f"💡 For production, set ENCRYPTION_KEY={key.decode()}")
        return key

cipher = Fernet(_get_encryption_key())


def hash_password(password: str) -> str:
    """Hash a password using argon2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def encrypt_token(token: str) -> str:
    """Encrypt a token using Fernet (AES-256)."""
    return cipher.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token using Fernet (AES-256)."""
    return cipher.decrypt(encrypted_token.encode()).decode()

