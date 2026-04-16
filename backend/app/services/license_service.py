"""
License service — business logic for feature gating and tier management

Provides:
- License creation (reverse-trial bootstrap on first launch)
- Tier resolution and module-access checks
- Trial expiry processing (daily job)
- License activation (Stripe purchase confirmation)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.license import License
from app.models.user import User
from app.modules.registry import COMMERCIAL_PRESETS

# Default reverse-trial duration
TRIAL_DURATION_DAYS = 14

# Tier → module preset mapping (mirrors COMMERCIAL_PRESETS keys)
TIER_PRESET_MAP: dict[str, str] = {
    "free": "basic",
    "gtd": "gtd",
    "full": "full",
}


class LicenseService:
    """Stateless service for license operations."""

    @staticmethod
    def get_or_create_license(db: Session, user_id: int) -> License:
        """
        Get existing license or bootstrap a new reverse-trial license.

        On first launch, user gets tier=full with 14-day trial.
        """
        license_record = (
            db.query(License).filter(License.user_id == user_id).first()
        )
        if license_record is not None:
            return license_record

        # Bootstrap reverse trial
        license_record = License(
            user_id=user_id,
            tier="full",
            trial_expires_at=datetime.now(timezone.utc) + timedelta(days=TRIAL_DURATION_DAYS),
        )
        db.add(license_record)
        db.commit()
        db.refresh(license_record)
        return license_record

    @staticmethod
    def get_license(db: Session, user_id: int) -> Optional[License]:
        """Get license for user, or None if no license exists."""
        return db.query(License).filter(License.user_id == user_id).first()

    @staticmethod
    def get_effective_tier(db: Session, user_id: int) -> str:
        """
        Resolve the effective tier for a user.

        Returns 'free' if no license exists (defensive — should not happen
        after first-run bootstrap).
        """
        license_record = (
            db.query(License).filter(License.user_id == user_id).first()
        )
        if license_record is None:
            return "free"
        return license_record.effective_tier

    @staticmethod
    def get_allowed_modules(db: Session, user_id: int) -> set[str]:
        """
        Get the set of module names the user's license allows.

        Maps effective_tier → commercial preset → module set.
        """
        effective_tier = LicenseService.get_effective_tier(db, user_id)
        preset_name = TIER_PRESET_MAP.get(effective_tier, "basic")
        return COMMERCIAL_PRESETS.get(preset_name, COMMERCIAL_PRESETS["basic"]).copy()

    @staticmethod
    def is_module_allowed(db: Session, user_id: int, module_name: str) -> bool:
        """
        Check if a user's license permits access to a specific module.

        This is the primary gate function called by route dependencies.

        Rules per spec:
        - gtd_inbox: requires tier in {gtd, full} OR active trial
        - memory_layer/ai_context: requires tier=full OR active trial
        - core/projects: always allowed
        """
        allowed = LicenseService.get_allowed_modules(db, user_id)
        return module_name in allowed

    @staticmethod
    def activate_license(
        db: Session,
        user_id: int,
        tier: str,
        purchase_id: str,
        stripe_customer_id: Optional[str] = None,
    ) -> License:
        """
        Activate a license after Stripe purchase confirmation.

        Sets the tier permanently and records the purchase.
        Trial expiry becomes irrelevant once activated.
        """
        if tier not in TIER_PRESET_MAP:
            raise ValueError(f"Invalid tier '{tier}'. Must be one of: {list(TIER_PRESET_MAP.keys())}")

        license_record = LicenseService.get_or_create_license(db, user_id)
        license_record.tier = tier
        license_record.purchase_id = purchase_id
        license_record.activated_at = datetime.now(timezone.utc)
        if stripe_customer_id:
            license_record.stripe_customer_id = stripe_customer_id
        db.commit()
        db.refresh(license_record)
        return license_record

    @staticmethod
    def process_expired_trials(db: Session) -> list[int]:
        """
        Daily job: downgrade all expired trials to free tier.

        Finds licenses where:
        - trial_expires_at < now
        - activated_at is NULL (not paid)
        - tier != 'free' (not already downgraded)

        Returns list of affected user_ids for event emission.
        """
        now = datetime.now(timezone.utc)
        expired = (
            db.query(License)
            .filter(
                License.trial_expires_at < now,
                License.activated_at.is_(None),
                License.tier != "free",
            )
            .all()
        )

        affected_user_ids = []
        for license_record in expired:
            license_record.tier = "free"
            affected_user_ids.append(license_record.user_id)

        if affected_user_ids:
            db.commit()

        return affected_user_ids
