"""
FastAPI dependencies — reusable guards for route protection.

Usage:
    @router.get("/protected")
    async def protected_route(user: User = Depends(get_current_user)):
        return {"user_id": str(user.id)}
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="JWT access token",
    auto_error=True,
)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that extracts and verifies the JWT from Authorization header.
    Returns the authenticated User object.

    Raises 401 for:
    - Missing token
    - Invalid/expired token
    - User not found or inactive
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    user = await db.scalar(select(User).where(User.id == user_id))

    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


async def get_current_verified_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    Like get_current_user but also requires email verification.
    Use for sensitive operations.
    """
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    return user