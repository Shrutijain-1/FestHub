
"""Seed demo data only when the database is completely empty."""

from backend.database import Base, SessionLocal, engine
from backend.models import College, Event, Registration, User
from backend.seed.seed_data import run_seed


def main():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        models = (College, Event, Registration, User)
        is_empty = all(db.query(model).count() == 0 for model in models)
    finally:
        db.close()

    if is_empty:
        print("Empty database found. Adding demo data...")
        run_seed()
    else:
        print("Database already has data. Skipping demo seed.")


if __name__ == "__main__":
    main()
