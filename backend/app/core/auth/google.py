"""
Google OAuth integration

Handles Google OAuth 2.0 authentication flow.
Shared infrastructure module - can be used by both Project Tracker and Proactive Assistant.
"""

import logging
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Scopes needed for authentication + Google Drive (for BYOS)
GOOGLE_SCOPES = [
    "openid",
    "email",
    "profile",
    # Future: Add Drive scope for BYOS integration
    # "https://www.googleapis.com/auth/drive.file",
]


def get_google_oauth_client() -> Optional[dict[str, str]]:
    """
    Get Google OAuth client configuration.

    Returns:
        Dict with client_id and client_secret if configured, None otherwise
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return None

    return {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
    }


def get_google_auth_url(state: Optional[str] = None) -> Optional[str]:
    """
    Generate Google OAuth authorization URL.

    Args:
        state: Optional state parameter for CSRF protection

    Returns:
        Authorization URL to redirect user to, or None if not configured
    """
    client = get_google_oauth_client()
    if client is None:
        return None

    params = {
        "client_id": client["client_id"],
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",  # Request refresh token
        "prompt": "consent",  # Force consent screen to get refresh token
    }

    if state:
        params["state"] = state

    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_google_code(code: str) -> Optional[dict[str, Any]]:
    """
    Exchange authorization code for tokens and user info.

    Args:
        code: Authorization code from Google callback

    Returns:
        Dict with user info and tokens, or None on error:
        {
            "google_id": str,
            "email": str,
            "display_name": str,
            "avatar_url": str,
            "access_token": str,
            "refresh_token": str (may be None),
        }
    """
    client = get_google_oauth_client()
    if client is None:
        logger.error("Google OAuth not configured")
        return None

    # Exchange code for tokens
    token_data = {
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    try:
        async with httpx.AsyncClient() as http_client:
            # Get tokens
            token_response = await http_client.post(
                GOOGLE_TOKEN_URL,
                data=token_data,
            )

            if token_response.status_code != 200:
                logger.error(
                    f"Google token exchange failed: {token_response.status_code} - {token_response.text}"
                )
                return None

            tokens = token_response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")

            if not access_token:
                logger.error("No access token in Google response")
                return None

            # Get user info
            userinfo_response = await http_client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_response.status_code != 200:
                logger.error(
                    f"Google userinfo failed: {userinfo_response.status_code} - {userinfo_response.text}"
                )
                return None

            userinfo = userinfo_response.json()

            return {
                "google_id": userinfo.get("id"),
                "email": userinfo.get("email"),
                "display_name": userinfo.get("name"),
                "avatar_url": userinfo.get("picture"),
                "access_token": access_token,
                "refresh_token": refresh_token,
            }

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during Google OAuth: {e}")
        return None
    except Exception as e:
        logger.error(f"Error during Google OAuth: {e}")
        return None


async def refresh_google_token(refresh_token: str) -> Optional[dict[str, Any]]:
    """
    Refresh Google access token using refresh token.

    Args:
        refresh_token: Google refresh token

    Returns:
        Dict with new access token, or None on error
    """
    client = get_google_oauth_client()
    if client is None:
        return None

    token_data = {
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                GOOGLE_TOKEN_URL,
                data=token_data,
            )

            if response.status_code != 200:
                logger.error(f"Google token refresh failed: {response.status_code}")
                return None

            return response.json()

    except Exception as e:
        logger.error(f"Error refreshing Google token: {e}")
        return None
