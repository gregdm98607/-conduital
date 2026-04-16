"""
License-aware authentication dependencies for FastAPI routes.

Provides dependency functions that check both authentication AND
license tier before allowing access to gated modules.

Usage in routes:
    from app.core.auth.license_dependencies import require_module

    @router.get("/inbox")
    def list_inbox(
        db: Session = Depends(get_db),
        user: User = Depends(require_module("gtd_inbox")),
    ):
        ...  # Only reachable if user's license allows gtd_inbox
"""

from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.license_service import LicenseService


def require_module(module_name: str) -> Callable:
    """
    Factory that returns a FastAPI dependency requiring a licensed module.

    Returns the authenticated User if access is granted.
    Raises 403 with gate metadata if the module is not licensed.

    The 403 response includes the required tier so the frontend can
    render the correct upgrade prompt and emit the gate_hit event.
    """

    async def _check_module_access(
        db: Session = Depends(get_db),
        current_user: Optional[User] = None,
    ) -> User:
        # Import here to avoid circular dependency at module level
        from app.core.auth.dependencies import get_current_user

        # If current_user wasn't injected, resolve it
        if current_user is None:
            # Auth may be optional in some configurations
            from app.core.config import settings

            if not settings.AUTH_ENABLED:
                # No auth → no license gating (development mode)
                return None  # type: ignore[return-value]

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        if not LicenseService.is_module_allowed(db, current_user.id, module_name):
            # Determine what tier is needed for the upgrade prompt
            required_tier = _required_tier_for_module(module_name)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "module_not_licensed",
                    "module": module_name,
                    "required_tier": required_tier,
                    "message": f"Your current plan does not include {module_name}. "
                    f"Upgrade to {required_tier} to unlock this feature.",
                },
            )

        return current_user

    return _check_module_access


def _required_tier_for_module(module_name: str) -> str:
    """
    Map a module name to the minimum tier required.

    Used in 403 responses to tell the frontend which upgrade to offer.
    """
    # Modules requiring 'full' tier
    full_only = {"memory_layer", "ai_context"}
    # Modules requiring 'gtd' tier (or higher)
    gtd_plus = {"gtd_inbox"}

    if module_name in full_only:
        return "full"
    if module_name in gtd_plus:
        return "gtd"
    return "free"
