# FestHub

**Plan. Discover. Experience.**

FestHub is a web platform where students discover and register for events at engineering colleges across Maharashtra, and organizers create and publish events with help from Google Gemini AI.

> **Demo data:** the colleges are real institutions used only as sample data. All events, people, emails and phone numbers are fictional, and this project has no affiliation with any college listed.

## Screenshots

<!-- Add screenshots to docs/screenshots/ and uncomment these lines.
![Home](docs/screenshots/home.png)
![Discover](docs/screenshots/discover.png)
![AI Assistant](docs/screenshots/ai.png)
-->

## Features

**Students**
- Register, log in, and edit their profile
- Browse upcoming events with a "This Month at Colleges" view
- Search by name, college or keyword, and filter by type, college, city, month and free or paid
- View full event details and register (seats, deadline and duplicate checks)
- See and cancel their registrations

**Organizers**
- Create events with a multi-section form, save as draft or publish, upload an image
- Edit, delete, publish or unpublish their own events
- See every registration for their events in a table and export it as CSV

**AI assistant (Google Gemini)**
- Generate event descriptions and highlights directly inside the Create Event form
- Generate schedules, invitations (WhatsApp, email, social media) and organizing checklists
- Get event ideas and ask event-planning questions in a chat

Gemini only receives text and returns text. It never reads or changes the database.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Frontend | Streamlit with custom CSS |
| Database | SQLite with SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Authentication | JWT (PyJWT), bcrypt password hashing |
| AI | Google Gemini API (`google-genai`) |
| Testing | pytest, httpx |

## Architecture

```
Streamlit (port 8501) --HTTP + JWT--> FastAPI (port 8000) --> SQLite
                                           |
                                           +--> Gemini API
```

- Streamlit never touches the database or Gemini. It only calls the FastAPI backend.
- The backend is layered: **routes** check who is asking, **services** hold the business rules, **models** describe the tables, and **schemas** validate requests and responses.
- Gemini is called from one file only, `backend/services/gemini_service.py`, with prompt templates in `prompts.py`.

## Project structure

```
festhub/
├── backend/
│   ├── main.py            # app, routers, error handlers
│   ├── database.py        # engine, sessions
│   ├── core/              # settings from .env
│   ├── models/            # user, college, event, registration
│   ├── schemas/           # user, event, registration, ai
│   ├── auth/              # password hashing, JWT, role guards
│   ├── routes/            # auth, events, organizer, registrations, colleges, dashboard, ai
│   ├── services/          # event, registration, password reset, gemini, prompts
│   ├── seed/              # demo data
│   ├── utils/             # image upload checks
│   └── static/uploads/    # event images
├── frontend/
│   ├── app.py             # page router
│   ├── views/             # one file per screen
│   ├── components/        # navbar, event cards, helpers
│   ├── services/          # API client, session
│   ├── styles/main.css
│   └── .streamlit/config.toml
├── database/              # SQLite file (created locally, not in git)
├── tests/                 # pytest tests
├── .env.example
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

## Setup (Windows PowerShell)

You need Python 3.11 or newer.

```powershell
git clone <your-repository-url>
cd festhub
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and set:

- `SECRET_KEY`: a long random value. Generate one with  
  `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `GEMINI_API_KEY`: a free key from [Google AI Studio](https://aistudio.google.com). The app runs without it, but the AI features will show a "not set up" message.
- `GEMINI_MODEL` and `GEMINI_FALLBACK_MODEL`: Gemini model names change over time. Open Google AI Studio, pick models your key can use, and put them here. Changing models never needs a code edit.

Never commit `.env`. It is listed in `.gitignore`.

Create the demo data. **This deletes all existing data in the database:**

```powershell
python -m backend.seed.seed_data
```

Run the app in two terminals, both from the project folder with the venv active:

```powershell
uvicorn backend.main:app --reload
```
```powershell
streamlit run frontend/app.py
```

Open http://localhost:8501. The API documentation is at http://localhost:8000/docs.

Demo event dates are relative to the day you run the seed script, so run it again whenever the events get old.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Organizer | organizer@example.com | Password123 |
| Student | student@example.com | Password123 |

These exist only in the demo data. Do not use them in a real deployment.

## Running the tests

```powershell
pip install -r requirements-dev.txt
python -m pytest -v
```

The tests use a temporary database and make no real Gemini calls. They cover authentication, role and ownership rules, search and filters, and the registration rules (duplicates, capacity, deadlines, cancelling).

## API overview

| Area | Endpoints |
|---|---|
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `GET` and `PUT /api/auth/me`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password` |
| Events | `GET /api/events` (with filters), `GET /api/events/by-month`, `GET /api/events/{id}`, `POST /api/events`, `PUT` and `DELETE /api/events/{id}`, `PATCH /api/events/{id}/status`, `POST /api/events/{id}/image` |
| Registrations | `POST /api/events/{id}/register`, `GET /api/my-registrations`, `DELETE /api/registrations/{id}`, `GET /api/events/{id}/registrations` (organizer) |
| Other | `GET /api/my-events`, `GET /api/colleges`, `GET /api/dashboard/stats`, `GET /api/health` |
| AI | `POST /api/ai/generate-description`, `generate-highlights`, `generate-schedule`, `generate-invitation`, `generate-checklist` (organizers), `POST /api/ai/event-ideas`, `POST /api/ai/chat` |

## Security notes

- Passwords are hashed with bcrypt and never stored in plain text.
- Role checks (student or organizer) and ownership checks run on the server, so hiding a button is never the only protection.
- Drafts are hidden from students, and other organizers cannot see or change an event they do not own.
- User text is escaped before it is shown as HTML, and CSV exports guard against spreadsheet formula injection.
- Image uploads are checked for extension, size and real file content, and saved under random names.
- The Gemini key is read from `.env` on the backend only and never reaches the browser.

## Known limitations

- **No payments.** Fees are shown, but registering for a paid event only reserves a seat.
- **Password reset is demo-only.** There is no email service, so in demo mode the 6-digit code is shown on screen and logged by the backend. Anyone who knows an email could reset that account, so turn `DEMO_MODE` off outside a demo.
- **Login is lost on a page refresh.** The token lives in Streamlit's session state. "Remember me" only pre-fills the email within a session.
- **No login rate limiting**, and tokens cannot be revoked before they expire (120 minutes by default).
- **SQLite** suits a single-machine project. The seat check is designed to be safe on SQLite, but it has not been load-tested.
- **AI output can be wrong**, so organizers must review it. Free-tier Gemini has rate limits, and model availability changes over time.
- **Images are stored on local disk.**
- **Tests cover the backend rules**, not the Streamlit screens or real Gemini output.

## Future improvements

Email delivery for registrations and password reset, payment gateway integration, QR-code check-in and attendance, PostgreSQL, cookie-based sessions with token refresh, rate limiting, and event reminders.

## Author

<your name>, final-year project, <your college>, <year>.