from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.db.base import Base
# Import all models to register with Base.metadata
from backend.app.models.detection import DetectionRun, Detection, ModelExperiment  # noqa: F401

# SQLite-specific connect args (check_same_thread=False for multi-threading)
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates database tables if they do not already exist, and migrates schema if needed."""
    try:
        Base.metadata.create_all(bind=engine)
        
        # Check if confidence_threshold column exists in detection_runs
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(detection_runs)"))
            columns = [row[1] for row in result.fetchall()]
            if "confidence_threshold" not in columns:
                try:
                    conn.execute(text("ALTER TABLE detection_runs ADD COLUMN confidence_threshold FLOAT DEFAULT 0.25"))
                    conn.commit()
                    logger.info("Migrated detection_runs: added confidence_threshold column.")
                except Exception as ex:
                    logger.warning(f"Column migration skipped: {ex}")

        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides an active database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
