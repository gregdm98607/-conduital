"""
Phase Template model - reusable phase definitions
"""

from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PhaseTemplate(Base, TimestampMixin):
    """
    Phase Template model - reusable project phase definitions

    Examples:
    - "Manuscript Development": ["Research", "Outline", "First Draft", "Revision", "Editing", "Submission"]
    - "Genealogy Research": ["Source Collection", "Digitization", "Analysis", "Narrative Writing", "Review"]
    - "Software Feature": ["Planning", "Design", "Implementation", "Testing", "Deployment"]
    """

    __tablename__ = "phase_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON array of phase definitions
    # Example: [{"name": "Research", "order": 1}, {"name": "Draft", "order": 2}, ...]
    phases_json: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<PhaseTemplate(id={self.id}, name='{self.name}')>"
