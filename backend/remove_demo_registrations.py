"""Removes the fake registrations created by the demo seed. Real registrations are not touched."""
from backend.database import SessionLocal
from backend.models import Registration, User

DEMO_STUDENT_EMAILS = ["priya@example.com", "arjun@example.com", "sneha@example.com"]

db = SessionLocal()
try:
    demo_ids = [
        user.id for user in db.query(User).filter(User.email.in_(DEMO_STUDENT_EMAILS)).all()
    ]
    rows = (
        db.query(Registration).filter(Registration.student_id.in_(demo_ids)).all()
        if demo_ids else []
    )

    if not rows:
        print("No demo registrations found. Nothing to remove.")
    else:
        total = db.query(Registration).count()
        print(f"Found {len(rows)} demo registration(s):")
        for row in rows:
            print(f"  - {row.student_name} -> {row.event.title} ({row.status})")
        print(f"Registrations now: {total}. After removal: {total - len(rows)}.")

        if input("Type YES to delete them: ").strip() == "YES":
            for row in rows:
                db.delete(row)
            db.commit()
            print("Removed.")
        else:
            print("Cancelled. Nothing was changed.")
finally:
    db.close()