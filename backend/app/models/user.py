"""
User model for authentication
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    User model for authentication and data ownership

    Supports Google OAuth (primary) with extensibility for other auth methods.
    Single-user design - no organization/team support initially.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Core identity
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Google OAuth fields
    google_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    google_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Encrypted in production

    # Future auth methods (backlogged)
    # password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # magic_link_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # magic_link_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Usage tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Subscription/tier (future monetization)
    # tier: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    # subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', display_name='{self.display_name}')>"

    @property
    def is_google_user(self) -> bool:
        """Check if user authenticated via Google"""
        return self.google_id is not None
