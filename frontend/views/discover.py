"""Discover Events: search bar, filters and a grid of event cards."""
from datetime import datetime

import streamlit as st

from components.event_card import render_event_card
from services.api_client import api_get

EVENT_TYPES = [
    "Workshop", "Hackathon", "Seminar", "Technical",
    "Cultural", "Sports", "Competition", "Other",
]


def _month_options(count: int = 6) -> dict[str, str]:
    """Next `count` months as {"November 2026": "2026-11", ...}."""
    now = datetime.now()
    options = {}
    for i in range(count):
        index = now.month - 1 + i
        first = datetime(now.year + index // 12, index % 12 + 1, 1)
        options[first.strftime("%B %Y")] = first.strftime("%Y-%m")
    return options


def render_discover() -> None:
    st.markdown("## Discover Events")
    st.markdown(
        '<div class="ef-tagline">Find workshops, hackathons and more across colleges.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    ok, colleges = api_get("/colleges")
    if not ok:
        st.error(colleges)
        return
    college_ids = {c["name"]: c["id"] for c in colleges}
    cities = sorted({c["city"] for c in colleges})
    months = _month_options()

    search = st.text_input(
        "Search",
        placeholder="🔍  Search by event name, college or keyword",
        label_visibility="collapsed",
    )
    col1, col2, col3, col4, col5 = st.columns(5)
    event_type = col1.selectbox("Event type", ["All"] + EVENT_TYPES)
    college = col2.selectbox("College", ["All"] + list(college_ids))
    city = col3.selectbox("Location", ["All"] + cities)
    month = col4.selectbox("Month", ["All"] + list(months))
    fee = col5.selectbox("Fee", ["All", "Free", "Paid"])

    params = {
        "q": search.strip() or None,
        "event_type": None if event_type == "All" else event_type,
        "college_id": None if college == "All" else college_ids[college],
        "city": None if city == "All" else city,
        "month": None if month == "All" else months[month],
        "fee": None if fee == "All" else fee.lower(),
        "limit": 100,
    }

    ok, events = api_get("/events", params=params)
    if not ok:
        st.error(events)
        return

    st.caption(f"{len(events)} event{'s' if len(events) != 1 else ''} found")

    if not events:
        st.markdown(
            '<div class="ef-empty">No events match your search. Try removing a filter.</div>',
            unsafe_allow_html=True,
        )
        return

    for start in range(0, len(events), 3):
        for col, event in zip(st.columns(3), events[start:start + 3]):
            with col:
                render_event_card(event, key_prefix="discover")