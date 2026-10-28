"""Home dashboard: greeting, stats, featured events, this month at colleges."""
from datetime import datetime
from html import escape

import streamlit as st

from components.event_card import render_event_card, render_month_section, stat_card
from services.api_client import api_get
from services.session import current_user


def _greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good Morning"
    return "Good Afternoon" if hour < 17 else "Good Evening"


def render_home() -> None:
    first_name = current_user()["name"].split()[0]
    st.markdown(f"## {_greeting()}, {escape(first_name)} 👋")
    st.markdown('<div class="ef-tagline">Plan. Discover. Experience.</div>', unsafe_allow_html=True)
    st.write("")

    # --- Stat cards ---
    ok, data = api_get("/dashboard/stats")
    if ok:
        for col, stat in zip(st.columns(4), data["stats"]):
            col.markdown(stat_card(stat["label"], stat["value"]), unsafe_allow_html=True)
    else:
        st.error(data)

    # --- Featured events ---
    st.markdown("### Featured Events")
    ok, events = api_get("/events", params={"limit": 3})
    if not ok:
        st.error(events)
    elif not events:
        st.markdown('<div class="ef-empty">No upcoming events yet.</div>', unsafe_allow_html=True)
    else:
        for col, event in zip(st.columns(3), events):
            with col:
                render_event_card(event, key_prefix="featured")

    # --- This Month at Colleges ---
    st.write("")
    st.markdown("### This Month at Colleges")
    ok, data = api_get("/events/by-month")
    if not ok:
        st.error(data)
    else:
        for month in data["months"]:
            render_month_section(month)