"""Loads settings from the .env file so no secret is written in code."""
import os
import logging
from pathlib import Path

from dotenv import load_dotenv

# Project root = three levels up from this file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "FestHub")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/eventflow.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip() or "gemini-3.5-flash-lite"
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "").strip() or "gemini-3.1-flash-lite"
DEMO_MODE = os.getenv("DEMO_MODE", "true").strip().lower() == "true"
if SECRET_KEY == "dev-only-secret" or len(SECRET_KEY) < 16:
    logging.getLogger("eventflow.config").warning(
        "SECRET_KEY is missing or weak. Set a long random value in .env."
    )