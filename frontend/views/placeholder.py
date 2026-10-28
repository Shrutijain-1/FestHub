"""Temporary pages for features built in later phases, and the Profile page."""
from html import escape

import streamlit as st

from services.session import current_user


def render_placeholder(title: str, phase: int) -> None:
    st.markdown(f"## {title}")
    st.markdown(
        f'<div class="ef-empty">🛠️ This page is built in <b>Phase {phase}</b>.</div>',
        unsafe_allow_html=True,
    )


def render_profile() -> None:
    user = current_user()
    st.markdown("## Profile")
    role = "Student" if user["role"] == "student" else "Event Organizer"
    st.markdown(
        '<div class="ef-event"><div class="ef-body">'
        f'<div class="ef-title">{escape(user["name"])}</div>'
        f'<div class="ef-college">{role}</div>'
        f'<div class="ef-meta">✉️ {escape(user["email"])}</div>'
        f'<div class="ef-meta">🏛️ {escape(user.get("college") or "Not provided")}</div>'
        f'<div class="ef-meta">📞 {escape(user.get("phone") or "Not provided")}</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )