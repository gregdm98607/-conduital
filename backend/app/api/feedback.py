"""
Feedback API endpoint (F-001)

Accepts in-app feedback submissions from users and stores them locally in SQLite.
No outbound call is made — feedback is available for review in the admin layer
and can be exported later.

Endpoints:
    POST /api/v1/feedback        — submit a feedback entry
    GET  /api/v1/feedback        — list all feedback (admin / local only)
    GET  /api/v1/feedback/{id}   — retrieve a single entry
"""

import logging
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.feedback import Feedback

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

FeedbackCategory = Literal["bug", "feature", "general"]


class FeedbackCreate(BaseModel):
    """Payload submitted by the frontend feedback widget."""

    category: FeedbackCategory = Field(
        ..., description="Feedback type: bug | feature | general"
    )
    message: str = Field(
        ..., min_length=1, max_length=2000, description="Feedback body text"
    )
    page: Optional[str] = Field(
        None, max_length=200, description="window.location.pathname at submission time"
    )
    email: Optional[str] = Field(
        None, max_length=254, description="Optional reply-to email"
    )
    app_version: Optional[str] = Field(
        None, max_length=20, description="App version string"
    )

    @field_validator("message")
    @classmethod
    def message_not_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Feedback message must contain non-whitespace text")
        return stripped

    @field_validator("page")
    @classmethod
    def page_safe(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Keep only pathname portion — strip any accidentally included query/hash
        return v.split("?")[0].split("#")[0][:200]


class FeedbackResponse(BaseModel):
    """Returned after a successful submission."""

    id: int
    category: str
    submitted_at: datetime

    model_config = {"from_attributes": True}


class FeedbackListItem(BaseModel):
    """Summary view for the feedback list."""

    id: int
    category: str
    message: str
    page: Optional[str]
    email: Optional[str]
    app_version: Optional[str]
    submitted_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit in-app feedback",
)
def submit_feedback(
    body: FeedbackCreate,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    """
    Accept a feedback submission from the in-app widget (F-001).

    Stores the entry in the local SQLite `feedback` table.
    Returns the assigned ID and timestamp so the frontend can confirm receipt.
    """
    entry = Feedback(
        category=body.category,
        message=body.message,
        page=body.page,
        email=body.email,
        app_version=body.app_version or settings.VERSION,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    logger.info(
        "Feedback submitted: id=%d category=%s page=%s",
        entry.id,
        entry.category,
        entry.page,
    )

    return FeedbackResponse(
        id=entry.id,
        category=entry.category,
        submitted_at=entry.submitted_at,
    )


@router.get(
    "",
    response_model=list[FeedbackListItem],
    summary="List all feedback entries (local admin view)",
)
def list_feedback(
    category: Optional[str] = Query(None, description="Filter by category"),
    page_num: int = Query(1, ge=1, alias="page"),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[FeedbackListItem]:
    """
    Return all stored feedback entries, newest first.

    Available to the local admin; no authentication required since Conduital
    is a single-user local app. Supports category filtering and pagination.
    """
    query = db.query(Feedback)
    if category:
        query = query.filter(Feedback.category == category)

    skip = (page_num - 1) * page_size
    entries = (
        query.order_by(Feedback.submitted_at.desc()).offset(skip).limit(page_size).all()
    )
    return [FeedbackListItem.model_validate(e) for e in entries]


@router.get(
    "/{feedback_id}",
    response_model=FeedbackListItem,
    summary="Retrieve a single feedback entry",
)
def get_feedback(feedback_id: int, db: Session = Depends(get_db)) -> FeedbackListItem:
    entry = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Feedback entry not found")
    return FeedbackListItem.model_validate(entry)
