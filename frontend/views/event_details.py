"""Full details page for one event, including the registration form."""
import re
from datetime import date, datetime
from html import escape

import streamlit as st

from components.event_card import banner_style, fee_label, format_date, format_time
from services.api_client import api_get, api_send
from services.session import current_user

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _back() -> None:
    st.session_state["page"] = st.session_state.get("details_back", "Discover Events")


def _info(label: str, value: str) -> str:
    return f'<div class="ef-info"><div class="k">{label}</div><div class="v">{escape(value)}</div></div>'


def render_event_details() -> None:
    st.button("← Back", on_click=_back)

    event_id = st.session_state.get("selected_event_id")
    if event_id is None:
        st.info("No event selected. Pick one from Discover Events.")
        return

    flash = st.session_state.pop("reg_flash", None)
    if flash:
        st.success(flash)

    ok, event = api_get(f"/events/{event_id}")
    if not ok:
        st.error(event)
        return

    seats = event["seats_available"]

    # Banner and heading
    banner_css, emoji = banner_style(event)
    st.markdown(
        f'<div class="ef-hero" style="{banner_css}">'
        f'<span class="ef-chip">{escape(event["event_type"])}</span>{emoji}</div>'
        f'<div class="ef-detail-title">{escape(event["title"])}</div>'
        f'<div class="ef-college">🏛️ {escape(event["college_name"])}</div>',
        unsafe_allow_html=True,
    )

    # Info tiles
    time_text = f'{format_time(event["start_time"])} – {format_time(event["end_time"])}'
    seats_text = f"{seats} of {event['capacity']} left" if seats > 0 else "Full"
    st.markdown(
        '<div class="ef-info-grid">'
        + _info("📅 Date", format_date(event["event_date"]))
        + _info("⏰ Time", time_text)
        + _info("📍 Venue", f'{event["venue"]}, {event["city"]}')
        + _info("💰 Registration fee", fee_label(event["registration_fee"]))
        + _info("🎟️ Available seats", seats_text)
        + _info("👤 Organizer", event["organizer_name"])
        + "</div>",
        unsafe_allow_html=True,
    )

    # Description
    if event["description"]:
        st.markdown(
            f'<div class="ef-section"><h4>About this event</h4><p>{escape(event["description"])}</p></div>',
            unsafe_allow_html=True,
        )

    # Highlights (one per line)
    highlights = [h.strip() for h in (event["highlights"] or "").splitlines() if h.strip()]
    if highlights:
        items = "".join(f"<li>{escape(h)}</li>" for h in highlights)
        st.markdown(
            f'<div class="ef-section"><h4>Event highlights</h4><ul>{items}</ul></div>',
            unsafe_allow_html=True,
        )

    # Registration deadline
    deadline_open = True
    if event["registration_deadline"]:
        deadline = datetime.fromisoformat(event["registration_deadline"])
        deadline_open = deadline >= datetime.now()
        if deadline_open:
            st.markdown(
                f'<div class="ef-deadline">⏳ Register before {format_date(event["registration_deadline"])}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="ef-deadline closed">Registration for this event has closed.</div>',
                unsafe_allow_html=True,
            )

    event_over = datetime.fromisoformat(event["event_date"]).date() < date.today()
    _render_registration(event, deadline_open, event_over)


def _render_registration(event: dict, deadline_open: bool, event_over: bool) -> None:
    user = current_user()
    if user["role"] != "student":
        st.caption("Organizer accounts can't register for events.")
        return

    ok, registrations = api_get("/my-registrations")
    if not ok:
        st.error(registrations)
        return

    already = any(
        r["event_id"] == event["id"] and r["status"] == "registered" for r in registrations
    )
    if already:
        st.success("✅ You are registered for this event. You can cancel it from My Registrations.")
        return
    if event_over:
        st.info("This event has already taken place.")
        return
    if not deadline_open:
        return  # the red "closed" notice above already explains it
    if event["seats_available"] == 0:
        st.warning("This event is full.")
        return

    fee = float(event["registration_fee"] or 0)
    is_paid = fee > 0

    with st.form(f"register_form_{event['id']}"):
        st.markdown("#### Register and pay" if is_paid else "#### Register for this event")
        name = st.text_input("Full name", value=user["name"])
        email = st.text_input("Email", value=user["email"])
        college = st.text_input("College", value=user.get("college") or "")
        phone = st.text_input("Phone number", value=user.get("phone") or "", placeholder="10-digit number")

        payment_method = None
        if is_paid:
            st.markdown(f"**Amount to pay: {fee_label(fee)}**")
            payment_method = st.radio("Payment method", ["UPI", "Card", "Net Banking"], horizontal=True)
            

        button_text = f"Pay {fee_label(fee)} & Register" if is_paid else "Register Now"
        submitted = st.form_submit_button(button_text, type="primary", use_container_width=True)

    if not submitted:
        return

    name, email, college, phone = name.strip(), email.strip(), college.strip(), phone.strip()
    if len(name) < 2:
        st.error("Please enter your full name.")
    elif not EMAIL_PATTERN.match(email):
        st.error("That doesn't look like a valid email address.")
    elif not (phone.isdigit() and len(phone) == 10):
        st.error("Phone number must be exactly 10 digits.")
    else:
        payload = {
            "student_name": name,
            "student_email": email,
            "student_college": college or None,
            "student_phone": phone,
            "payment_method": payment_method,
        }
        ok, result = api_send("POST", f"/events/{event['id']}/register", json=payload)
        if ok:
            message = "Registration Successful! You can find it under My Registrations."
            if is_paid:
                message = (
                    f"Registration Successful! Your payment of {fee_label(result['amount_paid'])} "
                    f"was received (receipt {result['payment_reference']}). "
                    "You can find it under My Registrations."
                )
            st.session_state["reg_flash"] = message
            st.rerun()
        else:
            st.error(result)