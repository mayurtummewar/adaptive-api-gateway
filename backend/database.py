import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def ensure_compatibility_columns() -> None:
    """Add columns introduced after the initial local demo schema."""
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE carts ADD COLUMN IF NOT EXISTS user_id INTEGER"))
        connection.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS user_id INTEGER"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
