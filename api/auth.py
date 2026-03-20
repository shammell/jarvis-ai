"""
Supabase JWT authentication for FastAPI
"""
import os
import jwt
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer(auto_error=False)

SUPABASE_JWT_ISSUER = os.getenv("SUPABASE_JWT_ISSUER")
SUPABASE_JWT_AUDIENCE = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")

class AuthUser:
    def __init__(self, user_id: str, token: str, email: Optional[str] = None):
        self.user_id = user_id
        self.token = token
        self.email = email

async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> AuthUser:
    """
    Verify Supabase JWT token and extract user_id
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token"
        )

    token = credentials.credentials
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured"
        )

    try:
        decode_kwargs = {
            "algorithms": ["HS256"],
            "audience": SUPABASE_JWT_AUDIENCE,
            "options": {"require": ["sub", "exp"]}
        }
        if SUPABASE_JWT_ISSUER:
            decode_kwargs["issuer"] = SUPABASE_JWT_ISSUER

        # Decode JWT token
        payload = jwt.decode(token, jwt_secret, **decode_kwargs)

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id"
            )

        return AuthUser(user_id=user_id, token=token, email=email)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Dependency for routes
CurrentUser = Depends(verify_token)
