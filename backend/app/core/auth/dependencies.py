"""
FastAPI authentication dependencies

Provides get_current_user and related dependencies for protecting API endpoints.
Shared infrastructure module - can be used by both Project Tracker and Proactive Assistant.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.auth.jwt import verify_token
from app.models.user import User

# Optional bearer token scheme - doesn't require auth header to be present
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user from JWT token if present.
    Returns None if no token provided or token is invalid.

    Use this for endpoints that work with or without authentication.
    """
    # If auth is disabled, return None (single-user mode)
    if not settings.AUTH_ENABLED:
        return None

    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current user from JWT token. Raises 401 if not authenticated.

    Use this for endpoints that require authentication.
    """
    # If auth is disabled, raise error (should use get_current_user_optional)
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not enabled. Set AUTH_ENABLED=True in config.",
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify they are active.
    Raises 403 if user account is deactivated.

    Use this for endpoints that require an active user account.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return current_user
