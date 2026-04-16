"""
License model for feature gating and commercial tier management

Supports the Conduital conversion funnel:
- free (basic): core + projects
- gtd ($49 one-time): core + projects + gtd_inbox
- full ($79 one-time): everything including memory_layer + ai_context

Reverse trial: first launch creates tier=full with 14-day expiry.
On expiry, auto-downgrades to free (basic) preserving all data.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class License(Base, TimestampMixin):
    """
    License state for a user's Conduital installation.

    One license per user. Created on first launch with reverse-trial defaults.
    Updated by Stripe webhook on purchase or by daily expiry job on trial end.
    """

    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Owner
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Commercial tier: free, gtd, full
    tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default="full"
    )

    # Trial tracking
    trial_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Stripe integration
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )

    # Purchase record — set when license key is activated
    purchase_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )

    # When the license was activated (key redeemed or purchase confirmed)
    activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationship back to User
    user: Mapped["User"] = relationship("User", back_populates="license")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<License(id={self.id}, user_id={self.user_id}, "
            f"tier='{self.tier}', trial_expires_at={self.trial_expires_at})>"
        )

    @property
    def is_trial_active(self) -> bool:
        """Check if user is on an active reverse trial."""
        if self.trial_expires_at is None:
            return False
        from datetime import timezone as tz
        return datetime.now(tz.utc) < self.trial_expires_at

    @property
    def is_paid(self) -> bool:
        """Check if user has completed a purchase (any tier)."""
        return self.activated_at is not None

    @property
    def effective_tier(self) -> str:
        """
        Resolve the tier the user should currently experience.

        - If paid, return stored tier (purchase is permanent).
        - If trial is active, return 'full' (reverse trial gives full access).
        - Otherwise, return 'free' (trial expired, no purchase).
        """
        if self.is_paid:
            return self.tier
        if self.is_trial_active:
            return "full"
        return "free"
