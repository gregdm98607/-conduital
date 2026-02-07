"""Test fixtures for migration tests."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import Base


@pytest.fixture
def in_memory_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    return engine


@pytest.fixture
def test_db(in_memory_engine):
    """Create test database with all tables."""
    Base.metadata.create_all(in_memory_engine)
    yield in_memory_engine
    Base.metadata.drop_all(in_memory_engine)


@pytest.fixture
def session(test_db):
    """Create a test database session."""
    Session = sessionmaker(bind=test_db)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def empty_db(in_memory_engine):
    """Create an empty database (no tables)."""
    return in_memory_engine


@pytest.fixture
def db_with_alembic_version(in_memory_engine):
    """Create database with alembic_version table."""
    with in_memory_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """))
        conn.execute(text("INSERT INTO alembic_version VALUES ('test_revision')"))
        conn.commit()
    return in_memory_engine
