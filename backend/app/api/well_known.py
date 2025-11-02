"""Well-known endpoints for OpenID Connect / OAuth2."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.utils.security import get_jwks

router = APIRouter()


@router.get("/.well-known/jwks.json")
def jwks():
    """
    JSON Web Key Set (JWKS) endpoint.
    
    Provides public keys for RS256 JWT verification.
    Required for interbank authentication and OpenBanking compliance.
    """
    return JSONResponse(content=get_jwks())


@router.get("/.well-known/openid-configuration")
def openid_configuration():
    """
    OpenID Connect Discovery document.
    
    Provides metadata about the OAuth2/OIDC server.
    """
    return {
        "issuer": "https://api.financehub.ru",
        "authorization_endpoint": "https://api.financehub.ru/auth/authorize",
        "token_endpoint": "https://api.financehub.ru/api/v1/auth/login",
        "jwks_uri": "https://api.financehub.ru/.well-known/jwks.json",
        "response_types_supported": ["code", "token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email", "accounts", "transactions", "payments"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "claims_supported": ["sub", "iss", "aud", "exp", "iat", "email", "name"],
        "grant_types_supported": ["authorization_code", "refresh_token", "client_credentials"]
    }

