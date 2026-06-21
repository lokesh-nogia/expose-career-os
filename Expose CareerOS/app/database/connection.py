import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Determine database path relative to this file
DB_DIR = os.path.dirname(os.path.abspath(__file__))
# Ensure database directory exists
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "career.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create SQLAlchemy engine
# check_same_thread=False is needed for SQLite multi-thread requests in FastAPI
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
