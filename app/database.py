"""
Database utilities and SQLAlchemy session management.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    import logging
    logging.error(
        "DATABASE_URL environment variable is required. "
        "Set it to your production database connection string."
    )
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Set it to your production database connection string."
    )

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # Required for SQLite when used across multiple threads (SocketIO workers).
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    echo=False,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)

Base = declarative_base()


def init_db() -> None:
    """
    Import models and create tables. Should be invoked once during startup.
    """
    import logging
    try:
        from app import models  # noqa: F401  (side-effect import)
        Base.metadata.create_all(bind=engine)
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing database: {e}", exc_info=True)
        raise


@contextmanager
def db_session() -> Generator:
    """
    Context manager that yields a SQLAlchemy session and guarantees cleanup.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

