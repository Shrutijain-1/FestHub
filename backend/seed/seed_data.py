"""Creates all tables and fills them with fictional, deterministic demo data.

Run: python -m backend.seed.seed_data

WARNING: this DELETES all existing data, including accounts you created and
uploaded event images. Dates are relative to today, so re-run it whenever the
demo events get old.
"""
import calendar
from datetime import date, datetime, time, timedelta

from backend.auth.security import hash_password
from backend.database import Base, SessionLocal, engine
from backend.models import College, Event, Registration, User
from backend.utils.image_upload import UPLOAD_DIR

DEMO_PASSWORD = "Password123"

COLLEGES = [
    {"name": "COEP Technological University", "city": "Pune", "description": "College of Engineering Pune"},
    {"name": "VIT Pune", "city": "Pune", "description": "Vishwakarma Institute of Technology"},
    {"name": "PICT", "city": "Pune", "description": "Pune Institute of Computer Technology"},
    {"name": "MIT-WPU", "city": "Pune", "description": "MIT World Peace University"},
    {"name": "Cummins College of Engineering for Women", "city": "Pune", "description": "Engineering college for women"},
    {"name": "Pimpri Chinchwad College of Engineering", "city": "Pune", "description": "PCCOE, Pune"},
    {"name": "VJTI Mumbai", "city": "Mumbai", "description": "Veermata Jijabai Technological Institute"},
    {"name": "Sardar Patel Institute of Technology", "city": "Mumbai", "description": "SPIT, Andheri"},
    {"name": "K. J. Somaiya College of Engineering", "city": "Mumbai", "description": "Somaiya Vidyavihar"},
    {"name": "Dwarkadas J. Sanghvi College of Engineering", "city": "Mumbai", "description": "DJSCE, Vile Parle"},
    {"name": "Terna Engineering College", "city": "Navi Mumbai", "description": "Terna, Nerul"},
    {"name": "VNIT Nagpur", "city": "Nagpur", "description": "Visvesvaraya National Institute of Technology"},
    {"name": "Yeshwantrao Chavan College of Engineering", "city": "Nagpur", "description": "YCCE, Nagpur"},
    {"name": "K. K. Wagh Institute of Engineering Education and Research", "city": "Nashik", "description": "KKWIEER, Nashik"},
    {"name": "Government College of Engineering, Chhatrapati Sambhajinagar", "city": "Chhatrapati Sambhajinagar", "description": "Government engineering college"},
    {"name": "Walchand College of Engineering", "city": "Sangli", "description": "WCE, Sangli"},
    {"name": "KIT's College of Engineering", "city": "Kolhapur", "description": "Kolhapur Institute of Technology"},
    {"name": "WIT Solapur", "city": "Solapur", "description": "Walchand Institute of Technology"},
    {"name": "SGGS Institute of Engineering and Technology", "city": "Nanded", "description": "SGGSIE&T, Nanded"},
    {"name": "Prof. Ram Meghe Institute of Technology and Research", "city": "Amravati", "description": "PRMIT&R, Badnera"},
    {"name": "Government College of Engineering, Karad", "city": "Karad", "description": "Government engineering college"},
    {"name": "SSBT's College of Engineering and Technology", "city": "Jalgaon", "description": "SSBT COET, Bambhori"},
    {"name": "Shri Sant Gajanan Maharaj College of Engineering", "city": "Shegaon", "description": "SSGMCE, Shegaon"},
]

# (title, type, college index, days from today, fee, capacity)
# Every college hosts at least one event, and every type appears three times.
EVENTS = [
    ("AI & Machine Learning Workshop", "Workshop", 0, 1, 0, 150),
    ("Cyber Security CTF", "Competition", 17, 2, 0, 100),
    ("Hands-on IoT Lab Session", "Technical", 2, 3, 0, 3),  # tiny capacity: shows "Full"
    ("Cloud Computing Seminar", "Seminar", 1, 4, 0, 120),
    ("Web Development Bootcamp", "Workshop", 5, 5, 100, 80),
    ("Inter-College Cricket Cup", "Sports", 15, 7, 0, 200),
    ("Startup Pitch Fest", "Other", 3, 9, 0, 150),
    ("Robotics Competition", "Competition", 6, 11, 150, 100),
    ("National Level Hackathon", "Hackathon", 7, 13, 200, 300),
    ("Cultural Night", "Cultural", 8, 15, 50, 400),
    ("TechFest 2026", "Technical", 11, 17, 100, 500),
    ("Careers in Data Science Seminar", "Seminar", 9, 19, 0, 200),
    ("Classical Music Evening", "Cultural", 12, 21, 0, 250),
    ("Badminton Open", "Sports", 4, 23, 50, 64),
    ("Smart Campus Hackathon", "Hackathon", 13, 25, 150, 200),
    ("Campus Photography Walk", "Other", 10, 27, 0, 60),
    ("Drone Technology Workshop", "Workshop", 14, 29, 100, 70),
    ("Embedded Systems Expo", "Technical", 16, 31, 0, 150),
    ("Women in Engineering Seminar", "Seminar", 18, 33, 0, 120),
    ("Folk Dance Festival", "Cultural", 19, 35, 50, 300),
    ("Kabaddi Championship", "Sports", 20, 37, 0, 150),
    ("Green Energy Hackathon", "Hackathon", 21, 39, 100, 120),
    ("Robo Race Challenge", "Competition", 22, 41, 100, 80),
    ("Innovation Showcase", "Other", 0, 43, 0, 100),
]
    
DESCRIPTIONS = {
    "Workshop": "{title} is a hands-on session hosted by {college}. Participants learn by building, with guidance from experienced mentors, and leave with practical skills they can use right away.",
    "Hackathon": "{title} brings student teams together at {college} to build working solutions to real problems in a single sprint. Expect mentors, energetic teamwork and a final demo round.",
    "Seminar": "{title} is an informative talk at {college} where industry guests and faculty share practical insights, followed by an open question and answer round.",
    "Technical": "{title} at {college} is a technical showcase with demos, talks and hands-on stations for students who like to see how things work.",
    "Cultural": "{title} at {college} celebrates student talent through performances, music and art, and is open to students from every college.",
    "Sports": "{title} at {college} is a friendly inter-college tournament. Bring your team, play fair and enjoy a day of healthy competition.",
    "Competition": "{title} at {college} challenges students to solve problems against the clock. Individuals and small teams can take part.",
    "Other": "{title} at {college} is a relaxed community event for students to meet people, share ideas and try something new.",
}

HIGHLIGHTS = {
    "Workshop": "Hands-on practice\nMentor support\nCertificate of participation",
    "Hackathon": "Team-based building\nMentors on call\nPrizes for the top teams",
    "Seminar": "Industry speakers\nOpen Q&A\nCertificate of attendance",
    "Technical": "Live demos\nHands-on stations\nMeet student innovators",
    "Cultural": "Live performances\nOpen to all colleges\nRefreshments available",
    "Sports": "Inter-college teams\nReferees and scorers\nTrophies and medals",
    "Competition": "Timed rounds\nIndividual and team entries\nPrizes and certificates",
    "Other": "Meet new people\nRelaxed format\nOpen to all students",
}

VENUES = {
    "Workshop": "Seminar Hall", "Hackathon": "Computer Lab Block", "Seminar": "Main Auditorium",
    "Technical": "Innovation Centre", "Cultural": "Open Air Theatre", "Sports": "Sports Ground",
    "Competition": "Lecture Hall 2", "Other": "Student Activity Centre",
}

TIMES = {
    "Hackathon": (time(9, 0), time(21, 0)),
    "Cultural": (time(17, 0), time(21, 0)),
    "Sports": (time(9, 0), time(17, 0)),
}
DEFAULT_TIMES = (time(10, 0), time(16, 0))

# (event title, student key, status)
REGISTRATIONS = [
    ("Hands-on IoT Lab Session", "priya", "registered"),
    ("Hands-on IoT Lab Session", "arjun", "registered"),
    ("Hands-on IoT Lab Session", "sneha", "registered"),  # fills all 3 seats
    ("AI & Machine Learning Workshop", "priya", "registered"),
    ("AI & Machine Learning Workshop", "arjun", "registered"),
    ("National Level Hackathon", "sneha", "registered"),
    ("Web Development Bootcamp", "arjun", "cancelled"),
]


def _clear_uploaded_images() -> None:
    if UPLOAD_DIR.exists():
        for path in UPLOAD_DIR.iterdir():
            if path.is_file() and path.name != ".gitkeep":
                path.unlink()


def run_seed() -> None:
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Clearing old data...")
        db.query(Registration).delete()
        db.query(Event).delete()
        db.query(User).delete()
        db.query(College).delete()
        db.commit()
        _clear_uploaded_images()

        print("Adding colleges...")
        colleges = [College(**c) for c in COLLEGES]
        db.add_all(colleges)
        db.commit()

        print("Adding demo users...")
        password_hash = hash_password(DEMO_PASSWORD)
        organizer = User(
            name="Rahul Sharma", email="organizer@example.com", password_hash=password_hash,
            role="organizer", college="VIT Pune", phone="9876500001",
        )
        main_student = User(
            name="Ananya Kulkarni", email="student@example.com", password_hash=password_hash,
            role="student", college="COEP Technological University", phone="9876500002",
        )
        students = {
            "priya": User(name="Priya Deshmukh", email="priya@example.com", password_hash=password_hash,
                          role="student", college="PICT", phone="9876500003"),
            "arjun": User(name="Arjun Patil", email="arjun@example.com", password_hash=password_hash,
                          role="student", college="VIT Pune", phone="9876500004"),
            "sneha": User(name="Sneha Joshi", email="sneha@example.com", password_hash=password_hash,
                          role="student", college="MIT-WPU", phone="9876500005"),
        }
        db.add_all([organizer, main_student, *students.values()])
        db.commit()

        print("Adding events...")
        today = date.today()
        days_left = calendar.monthrange(today.year, today.month)[1] - today.day
        events_by_title: dict[str, Event] = {}

        def add_event(title, etype, college, event_date, fee, capacity, status):
            start, end = TIMES.get(etype, DEFAULT_TIMES)
            deadline_day = max(event_date - timedelta(days=1), today)  # never in the past
            event = Event(
                organizer_id=organizer.id,
                college_id=college.id,
                title=title,
                description=DESCRIPTIONS[etype].format(title=title, college=college.name),
                highlights=HIGHLIGHTS[etype],
                event_type=etype,
                event_date=datetime.combine(event_date, time.min),
                start_time=start,
                end_time=end,
                venue=f"{college.name} {VENUES[etype]}",
                city=college.city,
                capacity=capacity,
                registration_fee=fee,
                registration_deadline=datetime.combine(deadline_day, time(23, 59)),
                status=status,
            )
            db.add(event)
            events_by_title[title] = event

        for index, (title, etype, college_index, offset, fee, capacity) in enumerate(EVENTS):
            if index < 4:  # keep the first few inside the current month
                offset = min(offset, days_left)
            add_event(title, etype, colleges[college_index], today + timedelta(days=offset),
                      fee, capacity, "published")

        # One draft, so "Save Draft" and the Draft badge can be demonstrated
        add_event("Women in Tech Panel", "Seminar", colleges[1],
                  today + timedelta(days=20), 0, 100, "draft")
        db.commit()

        print("Adding demo registrations...")
        for number, (title, key, status) in enumerate(REGISTRATIONS, start=1):
            event, student = events_by_title[title], students[key]
            fee = float(event.registration_fee or 0)
            if fee == 0:
                payment_status = "not_required"
            elif status == "registered":
                payment_status = "paid"
            else:
                payment_status = "refund_initiated"  # a cancelled paid registration

            db.add(Registration(
                event_id=event.id, student_id=student.id,
                student_name=student.name, student_email=student.email,
                student_college=student.college, student_phone=student.phone,
                status=status,
                amount_paid=fee,
                payment_status=payment_status,
                payment_method="UPI" if fee > 0 else None,
                payment_reference=f"PAY-DEMO{number:04d}" if fee > 0 else None,
                refund_reference=f"RFD-DEMO{number:04d}" if payment_status == "refund_initiated" else None,
            ))
        db.commit()

        print(f"Done. {len(colleges)} colleges, {2 + len(students)} users, "
              f"{len(EVENTS)} published events + 1 draft, {len(REGISTRATIONS)} registrations.")
        print("Organizer login: organizer@example.com / Password123")
        print("Student login:   student@example.com / Password123")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()