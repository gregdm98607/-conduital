"""
Authentication module for Project Tracker

Provides Google OAuth authentication with JWT tokens.
Designed as shared infrastructure for Proactive Assistant integration.
"""

from app.core.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token,
)
from app.core.auth.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_current_active_user,
)
from app.core.auth.google import (
    get_google_oauth_client,
    get_google_auth_url,
    exchange_google_code,
)

__all__ = [
    # JWT
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "decode_token",
    # Dependencies
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    # Google OAuth
    "get_google_oauth_client",
    "get_google_auth_url",
    "exchange_google_code",
]
