from sqlalchemy import create_engine
from sqlmodel import SQLModel

# Import all models to register them with SQLModel metadata
from app.db_models.api_key import APIKey

# Database URL for SQLite
DATABASE_URL = "sqlite:///./gateway.db"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """Create database tables based on SQLModel metadata."""
    SQLModel.metadata.create_all(engine) 