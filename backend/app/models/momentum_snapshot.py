"""
MomentumSnapshot model — daily momentum snapshots for trend/sparkline data
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MomentumSnapshot(Base):
    """
    Daily momentum snapshot for a project.

    Stores the momentum score and factor breakdown at a point in time,
    enabling trend indicators and sparkline charts.
    """

    __tablename__ = "momentum_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    factors_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON blob of factor breakdown
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
