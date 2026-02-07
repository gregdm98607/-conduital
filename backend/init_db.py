"""
Initialize the database with tables
Run this script once to set up the database
"""

from pathlib import Path
from app.core.database import Base, engine
from app.core.config import settings
from app.models import project, task, area, goal, vision, context, inbox_item

def init_database():
    """Create all database tables"""
    # Ensure database directory exists
    db_path = Path(settings.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"📁 Database directory: {db_path.parent}")
    print(f"📊 Database file: {db_path}")

    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    print("✅ Database initialized successfully!")
    print(f"\nYou can now start the server with:")
    print("  poetry run uvicorn app.main:app --reload")
    print("  OR")
    print("  python -m uvicorn app.main:app --reload")

if __name__ == "__main__":
    init_database()
