"""Security utilities: password hashing, JWT, encryption."""
from datetime import datetime, timedelta
from typing import Optional, Literal
from pathlib import Path
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
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


# RSA Key Management for RS256 JWT
def _load_rsa_keys():
    """Load RSA private and public keys from files."""
    keys_dir = Path(__file__).parent.parent.parent / "keys"
    private_key_path = keys_dir / "private_key.pem"
    public_key_path = keys_dir / "public_key.pem"
    
    if not private_key_path.exists() or not public_key_path.exists():
        print("⚠️ RSA keys not found. Run: docker exec financehub_backend python scripts/generate_rsa_keys.py")
        return None, None
    
    # Load private key
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    
    # Load public key
    with open(public_key_path, "rb") as f:
        public_key = serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )
    
    return private_key, public_key


_rsa_private_key, _rsa_public_key = _load_rsa_keys()


def create_bank_token(bank_code: str, audience: str = "interbank", expires_delta: Optional[timedelta] = None) -> str:
    """
    Create RS256 JWT token for interbank communication.
    
    Args:
        bank_code: Bank identifier (e.g., 'financehub', 'vbank')
        audience: Token audience (default: 'interbank')
        expires_delta: Custom expiration (default: 60 minutes)
    
    Returns:
        Signed RS256 JWT token
    """
    if not _rsa_private_key:
        raise RuntimeError("RSA private key not loaded. Cannot create bank token.")
    
    to_encode = {
        "sub": bank_code,
        "type": "bank",
        "iss": bank_code,
        "aud": audience
    }
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    
    to_encode["exp"] = expire
    
    # Sign with RS256
    encoded_jwt = jwt.encode(to_encode, _rsa_private_key, algorithm="RS256")
    return encoded_jwt


def verify_bank_token(token: str) -> Optional[dict]:
    """
    Verify RS256 JWT bank token.
    
    Args:
        token: RS256 JWT token to verify
    
    Returns:
        Decoded payload if valid, None otherwise
    """
    if not _rsa_public_key:
        print("⚠️ RSA public key not loaded. Cannot verify bank token.")
        return None
    
    try:
        payload = jwt.decode(token, _rsa_public_key, algorithms=["RS256"])
        
        # Validate it's a bank token
        if payload.get("type") != "bank":
            print("⚠️ Token is not a bank token")
            return None
        
        return payload
    except JWTError as e:
        print(f"⚠️ Bank token verification failed: {e}")
        return None


def get_jwks() -> dict:
    """
    Generate JWKS (JSON Web Key Set) for RS256 public key.
    
    Returns:
        JWKS dictionary for /.well-known/jwks.json endpoint
    """
    if not _rsa_public_key:
        return {"keys": []}
    
    from cryptography.hazmat.primitives.asymmetric import rsa
    from jose.jwk import RSAKey
    
    # Convert to JWK format
    jwk = RSAKey(key=_rsa_public_key, algorithm="RS256")
    jwk_dict = jwk.to_dict()
    
    # Add required fields for JWKS
    jwk_dict["use"] = "sig"  # signature
    jwk_dict["kid"] = "financehub-2025"  # key ID
    jwk_dict["alg"] = "RS256"
    
    return {
        "keys": [jwk_dict]
    }

