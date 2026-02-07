"""
Database configuration and session management
"""

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Create database directory if it doesn't exist
db_path = Path(settings.DATABASE_PATH)
db_path.parent.mkdir(parents=True, exist_ok=True)

# Create SQLAlchemy engine
# WAL mode for better concurrent read performance
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=settings.DATABASE_ECHO,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session

    Usage in FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database - create all tables
    Note: In production, use Alembic migrations instead
    """
    from app.models import Base

    Base.metadata.create_all(bind=engine)


def enable_wal_mode() -> None:
    """
    Enable Write-Ahead Logging for better concurrent performance

    WAL mode allows multiple readers even when a writer is active
    """
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.commit()