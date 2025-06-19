from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.headers.get("Authorization")
        if not token or token != "Bearer dev-token":
            raise HTTPException(status_code=401, detail="Unauthorized")
        return await call_next(request)
