
"""Seed demo data only when the database is completely empty."""

from backend.database import Base, SessionLocal, engine
from backend.models import College, Event, Registration, User
from backend.seed.seed_data import run_seed


def main():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        counts = [
            db.query(model).count()
            for model in (College, Event, Registration, User)
        ]

        if not any(counts):
            print("Empty database found. Adding demo data...")
            run_seed()
        else:
            print("Database already has data. Skipping demo seed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
