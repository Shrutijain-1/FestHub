"""Database engine, session and Base class, shared by all models."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.core.config import DATABASE_URL

# check_same_thread=False is required for SQLite when used with FastAPI,
# since FastAPI can handle requests on different threads.

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
    )
    else:
        postgres_url = DATABASE_URL.replace(
            "postgresql+psycopg://", "postgresql+psycopg2://", 1
    )

    if postgres_url.startswith("postgresql://"):
        postgres_url = postgres_url.replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )

    engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # NEW: test the connection first; reconnect if Neon closed it
    pool_recycle=300,     # NEW: replace connections older than 5 minutes
    # keep any other arguments you already have here
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