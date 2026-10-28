"""Deletes ONLY the three demo student accounts (Priya, Arjun, Sneha). Nothing else is touched."""
from backend.database import SessionLocal
from backend.models import Event, Registration, User

DEMO_EMAILS = ["priya@example.com", "arjun@example.com", "sneha@example.com"]

db = SessionLocal()
try:
    users = (
        db.query(User)
        .filter(User.email.in_(DEMO_EMAILS), User.role == "student")
        .all()
    )

    if not users:
        print("The demo accounts were not found. Nothing to remove.")
    else:
        total = db.query(User).count()
        blocked = False
        print(f"Found {len(users)} demo account(s):")
        for user in users:
            registrations = db.query(Registration).filter(Registration.student_id == user.id).count()
            events = db.query(Event).filter(Event.organizer_id == user.id).count()
            print(f"  - {user.name} ({user.email}): {registrations} registration(s), {events} event(s)")
            if registrations or events:
                blocked = True

        if blocked:
            print("\nStopped. These accounts still have registrations or events, so nothing was deleted.")
            print("Run 'python -m backend.remove_demo_registrations' first, then run this again.")
        else:
            print(f"\nUsers now: {total}. After removal: {total - len(users)}.")
            if input("Type YES to delete these accounts: ").strip() == "YES":
                for user in users:
                    db.delete(user)
                db.commit()
                print("Removed.")
            else:
                print("Cancelled. Nothing was changed.")
finally:
    db.close()