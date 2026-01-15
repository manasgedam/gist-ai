from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# This creates a local file named 'gist_ai.db' in your project folder. Total cost: $0.
SQLALCHEMY_DATABASE_URL = "sqlite:///./gist_ai.db"

# 'check_same_thread=False' is required specifically for SQLite + FastAPI
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from .models import Base
    Base.metadata.create_all(bind=engine)