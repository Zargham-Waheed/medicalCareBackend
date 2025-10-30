import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_NAME = os.getenv("DB_NAME", "app_db")
DB_USER = os.getenv("DB_USER", "api_user")
DB_PASS = os.getenv("DB_PASS")  # we will inject this at deploy time
INSTANCE_CONN_NAME = os.getenv("INSTANCE_CONN_NAME")  # vpsproject-476606:us-central1:db-vps-prod-001
DB_SOCKET_DIR = "/cloudsql"

DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASS}@/{DB_NAME}"
    f"?host={DB_SOCKET_DIR}/{INSTANCE_CONN_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=2,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency for getting a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()