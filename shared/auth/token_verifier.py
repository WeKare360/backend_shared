
from fastapi import Request, HTTPException, status
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

def get_jwt_secret() -> str:
    """Get JWT secret from environment (allows testing)"""
    return os.getenv("JWT_SECRET", "secret")

def get_jwt_algorithm() -> str:
    """Get JWT algorithm from environment (allows testing)"""
    return os.getenv("JWT_ALGORITHM", "HS256")

def get_token_from_request(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token_parts = auth.split(" ")
    if len(token_parts) < 2:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    return token_parts[1]

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=[get_jwt_algorithm()], options={"verify_aud": False})
    except Exception:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
