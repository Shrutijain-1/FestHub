"""All communication between Streamlit and FastAPI goes through this file."""
import os

import requests
import streamlit as st
from dotenv import load_dotenv

from services.session import clear_session, get_token

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
SERVER_URL = API_BASE_URL.removesuffix("/api")  # e.g. http://localhost:8000


def image_url(image_path: str) -> str:
    """Turn 'uploads/abc.png' into a full URL the browser can load."""
    return f"{SERVER_URL}/static/{image_path}"


def check_health() -> tuple[bool, dict | None]:
    """Return (True, data) if the backend responds, else (False, None)."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException:
        return False, None


def register_user(name: str, email: str, password: str, role: str, college: str, phone: str):
    """Returns (success, data_or_error_message)."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={
                "name": name, "email": email, "password": password,
                "role": role, "college": college, "phone": phone,
            },
            timeout=5,
        )
        if response.status_code == 201:
            return True, response.json()
        return False, _error_message(response, "Registration failed.")
    except requests.RequestException:
        return False, "Cannot reach the server. Please try again."


def login_user(email: str, password: str):
    """Returns (success, data_or_error_message)."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=5,
        )
        if response.status_code == 200:
            return True, response.json()
        return False, _error_message(response, "Login failed.")
    except requests.RequestException:
        return False, "Cannot reach the server. Please try again."


def api_get(path: str, params: dict | None = None):
    """Authenticated GET. Returns (success, data_or_error_message)."""
    headers = {"Authorization": f"Bearer {get_token()}"}
    try:
        response = requests.get(
            f"{API_BASE_URL}{path}", params=params, headers=headers, timeout=8
        )
    except requests.RequestException:
        return False, "Cannot reach the server. Please try again."

    if response.status_code == 200:
        return True, response.json()
    if response.status_code == 401:
        clear_session()  # token expired or invalid, so send the user back to login
        st.rerun()
    return False, _error_message(response, "Something went wrong.")


def api_send(method: str, path: str, json: dict | None = None,
             files: dict | None = None, timeout: int = 15):
    """Authenticated POST / PUT / PATCH / DELETE. Returns (success, data_or_error_message)."""
    headers = {"Authorization": f"Bearer {get_token()}"}
    try:
        response = requests.request(
            method, f"{API_BASE_URL}{path}", json=json, files=files,
            headers=headers, timeout=timeout,
        )
    except requests.RequestException:
        return False, "Cannot reach the server. Please try again."

    if response.status_code == 204:
        return True, None
    if response.status_code in (200, 201):
        return True, response.json()
    if response.status_code == 401:
        clear_session()
        st.rerun()
    return False, _error_message(response, "Something went wrong.")


def _error_message(response: requests.Response, fallback: str) -> str:
    """Pull a friendly message out of an error response."""
    try:
        detail = response.json().get("detail", fallback)
    except ValueError:
        return fallback
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list) and detail and isinstance(detail[0], dict):
        # Validation errors arrive as a list; show the first message
        return detail[0].get("msg", fallback).removeprefix("Value error, ")
    return fallback
def api_post_public(path: str, json: dict):
    """POST without a login token (used for password reset). Returns (success, data_or_message)."""
    try:
        response = requests.post(f"{API_BASE_URL}{path}", json=json, timeout=10)
    except requests.RequestException:
        return False, "Cannot reach the server. Please try again."
    if response.status_code in (200, 201):
        return True, response.json()
    return False, _error_message(response, "Something went wrong.")