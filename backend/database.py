"""Database engine, session and Base class, shared by all models."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.core.config import DATABASE_URL

if DATABASE_URL.startswith("sqlite"):
    # check_same_thread=False is required for SQLite when used with FastAPI,
    # since FastAPI can handle requests on different threads.
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # Neon (PostgreSQL): make sure SQLAlchemy uses the psycopg2 driver we installed
    postgres_url = DATABASE_URL
    for old_prefix in ("postgresql+psycopg://", "postgres://", "postgresql://"):
        if postgres_url.startswith(old_prefix):
            postgres_url = postgres_url.replace(old_prefix, "postgresql+psycopg2://", 1)
            break

    engine = create_engine(
        postgres_url,
        pool_pre_ping=True,   # test a connection first; reconnect if Neon closed it
        pool_recycle=300,     # replace connections older than 5 minutes
    )


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, connection_record):
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: gives each request its own DB session, then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()