"""Database configuration and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

from app.observability.logging import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/tickets",
)

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and ensure default admin exists."""
    from app.models import user, ticket, ticket_assignment, message  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("database_tables_created", extra={"tables": list(Base.metadata.tables.keys())})
    _ensure_default_admin()


def _ensure_default_admin():
    """Create default admin user (admin / admin) if no admin exists."""
    from app.models.user import User
    from app.services.auth_service import hash_password

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@localhost").first()
        if existing:
            return
        admin = User(
            name="admin",
            email="admin@localhost",
            password_hash=hash_password("admin"),
            role="admin",
        )
        db.add(admin)
        db.commit()
        logger.info("default_admin_created", extra={"email": "admin@localhost"})
    except Exception as e:
        logger.warning("default_admin_creation_failed", extra={"error": str(e)})
        db.rollback()
    finally:
        db.close()
