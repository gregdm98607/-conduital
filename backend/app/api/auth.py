"""
Authentication API routes

Handles Google OAuth login flow and token management.
Shared infrastructure module - designed for use by both Conduital and Proactive Assistant.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.core.auth.google import get_google_auth_url, exchange_google_code
from app.core.auth.dependencies import get_current_user, get_current_user_optional
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# ============================================================================
# Schemas
# ============================================================================


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User info response"""
    id: int
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthStatusResponse(BaseModel):
    """Authentication status response"""
    enabled: bool
    google_configured: bool
    user: Optional[UserResponse] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


# ============================================================================
# Routes
# ============================================================================


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get authentication system status.

    Returns whether auth is enabled, configured, and current user if authenticated.
    """
    google_configured = bool(
        settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET
    )

    return AuthStatusResponse(
        enabled=settings.AUTH_ENABLED,
        google_configured=google_configured,
        user=UserResponse.model_validate(current_user) if current_user else None,
    )


@router.get("/google/login")
async def google_login(
    redirect_url: Optional[str] = Query(None, description="URL to redirect after login"),
):
    """
    Initiate Google OAuth login flow.

    Redirects user to Google's consent screen.
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not enabled",
        )

    auth_url = get_google_auth_url(state=redirect_url)

    if auth_url is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter (redirect URL)"),
    db: Session = Depends(get_db),
):
    """
    Handle Google OAuth callback.

    Exchanges authorization code for tokens, creates/updates user, and redirects to frontend.
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not enabled",
        )

    # Exchange code for tokens and user info
    google_data = await exchange_google_code(code)

    if google_data is None:
        # Redirect to frontend with error
        error_url = f"{settings.FRONTEND_URL}/login?error=google_auth_failed"
        return RedirectResponse(url=error_url)

    # Find or create user
    user = db.query(User).filter(User.google_id == google_data["google_id"]).first()

    if user is None:
        # Check if user exists with this email (might have used different auth method)
        user = db.query(User).filter(User.email == google_data["email"]).first()

        if user is None:
            # Create new user
            user = User(
                email=google_data["email"],
                display_name=google_data["display_name"],
                avatar_url=google_data["avatar_url"],
                google_id=google_data["google_id"],
                google_refresh_token=google_data.get("refresh_token"),
                is_verified=True,  # Google-verified email
            )
            db.add(user)
            logger.info(f"Created new user: {user.email}")
        else:
            # Link Google to existing user
            user.google_id = google_data["google_id"]
            user.google_refresh_token = google_data.get("refresh_token")
            if not user.display_name:
                user.display_name = google_data["display_name"]
            if not user.avatar_url:
                user.avatar_url = google_data["avatar_url"]
            logger.info(f"Linked Google to existing user: {user.email}")
    else:
        # Update existing user
        if google_data.get("refresh_token"):
            user.google_refresh_token = google_data["refresh_token"]
        if google_data.get("display_name"):
            user.display_name = google_data["display_name"]
        if google_data.get("avatar_url"):
            user.avatar_url = google_data["avatar_url"]

    # Update login tracking
    user.last_login_at = datetime.now(timezone.utc)
    user.login_count += 1

    db.commit()
    db.refresh(user)

    # Create JWT tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Redirect to frontend with tokens
    # Frontend will extract tokens from URL fragment and store them
    redirect_url = state or settings.FRONTEND_URL

    # Pass tokens via URL fragment (not query params for security)
    token_params = urlencode({
        "access_token": access_token,
        "refresh_token": refresh_token,
    })
    final_url = f"{redirect_url}#auth={token_params}"

    return RedirectResponse(url=final_url)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not enabled",
        )

    payload = verify_token(request.refresh_token, token_type="refresh")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Verify user exists and is active
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user info.
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """
    Logout current user.

    Note: JWT tokens are stateless, so this mainly serves as a confirmation endpoint.
    Frontend should delete stored tokens.
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"}
