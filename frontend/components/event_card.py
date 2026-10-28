"""Reusable HTML pieces: stat cards, event cards and month rows."""
from datetime import datetime, time
from html import escape

import streamlit as st
from services.api_client import image_url

# Banner colour + emoji per event type (used until an uploaded image exists)
TYPE_STYLE = {
    "Workshop": ("#4F46E5", "#7C3AED", "🛠️"),
    "Hackathon": ("#0F1B3D", "#4F46E5", "💻"),
    "Seminar": ("#0EA5E9", "#4F46E5", "🎤"),
    "Technical": ("#2563EB", "#7C3AED", "⚙️"),
    "Cultural": ("#DB2777", "#7C3AED", "🎭"),
    "Sports": ("#059669", "#0EA5E9", "🏆"),
    "Competition": ("#D97706", "#DC2626", "🥇"),
    "Other": ("#475569", "#4F46E5", "✨"),
}


def format_date(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%d %b %Y")


def format_time(value: str | None) -> str:
    return time.fromisoformat(value).strftime("%I:%M %p").lstrip("0") if value else "TBA"


def fee_label(fee: float) -> str:
    return "Free" if fee == 0 else f"₹{fee:,.0f}"


def stat_card(label: str, value) -> str:
    return (
        f'<div class="ef-stat"><div class="value">{value}</div>'
        f'<div class="label">{escape(label)}</div></div>'
    )


def _open_details(event_id: int) -> None:
    st.session_state["selected_event_id"] = event_id
    st.session_state["details_back"] = st.session_state.get("page", "Home")
    st.session_state["page"] = "Event Details"

def banner_style(event: dict) -> tuple[str, str]:
    """Returns (css, emoji). Uses the uploaded image if there is one."""
    c1, c2, emoji = TYPE_STYLE.get(event["event_type"], TYPE_STYLE["Other"])
    if event.get("image_path"):
        url = image_url(event["image_path"])
        css = f"background:linear-gradient(rgba(15,27,61,.2),rgba(15,27,61,.2)),url('{url}') center/cover;"
        return css, ""
    return f"background:linear-gradient(135deg,{c1},{c2});", emoji    


def render_event_card(event: dict, key_prefix: str) -> None:
    banner_css, emoji = banner_style(event)
    seats = event["seats_available"]
    seats_text = f"{seats} seats left" if seats > 0 else "Full"
    seats_class = "ef-seats" if seats > 0 else "ef-seats full"

    html = (
        '<div class="ef-event">'
        f'<div class="ef-banner" style="{banner_css}">'
        f'<span class="ef-chip">{escape(event["event_type"])}</span>{emoji}</div>'
        '<div class="ef-body">'
        f'<div class="ef-title">{escape(event["title"])}</div>'
        f'<div class="ef-college">🏛️ {escape(event["college_name"])}</div>'
        f'<div class="ef-meta">📅 {format_date(event["event_date"])} · ⏰ {format_time(event["start_time"])}</div>'
        f'<div class="ef-meta">📍 {escape(event["city"])}</div>'
        '<div class="ef-foot">'
        f'<span class="ef-fee">{fee_label(event["registration_fee"])}</span>'
        f'<span class="{seats_class}">{seats_text}</span>'
        '</div></div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)
    st.button(
        "View Details",
        key=f"{key_prefix}_{event['id']}",
        use_container_width=True,
        on_click=_open_details,
        args=(event["id"],),
    )


def render_month_section(month: dict) -> None:
    st.markdown(f'<div class="ef-month-title">{escape(month["label"])}</div>', unsafe_allow_html=True)
    if not month["events"]:
        st.markdown('<div class="ef-empty">No events scheduled yet.</div>', unsafe_allow_html=True)
        return
    for event in month["events"]:
        d = datetime.fromisoformat(event["event_date"])
        st.markdown(
            '<div class="ef-row">'
            f'<div class="ef-date-badge">{d.day}<small>{d.strftime("%b")}</small></div>'
            '<div>'
            f'<div class="ef-row-title">{escape(event["title"])}</div>'
            f'<div class="ef-row-sub">{escape(event["college_name"])} · {escape(event["event_type"])} · {fee_label(event["registration_fee"])}</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )