"""Organizer page: the attendee table for one event."""
import csv
import io

import streamlit as st

from components.event_card import format_date, stat_card
from components.formatting import local_datetime_text
from services.api_client import api_get
from services.session import current_user

PAYMENT_LABELS = {"not_required": "Free", "paid": "Paid", "refund_initiated": "Refund initiated"}


def _back() -> None:
    st.session_state["page"] = "Create Event"  # 'goto_tab' already opens My Events


def _safe_cell(value: str) -> str:
    """Stops Excel from treating a cell like '=SUM(...)' as a formula."""
    return "'" + value if value[:1] in ("=", "+", "-", "@") else value


def _to_csv(rows: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _safe_cell(str(value)) for key, value in row.items()})
    return buffer.getvalue().encode("utf-8-sig")  # utf-8-sig opens cleanly in Excel


def render_event_registrations() -> None:
    st.button("← Back to My Events", on_click=_back)

    if current_user()["role"] != "organizer":
        st.error("Only event organizers can view registrations.")
        return

    event_id = st.session_state.get("selected_event_id")
    if event_id is None:
        st.info("No event selected. Open My Events and click Registrations.")
        return

    ok, event = api_get(f"/events/{event_id}")
    if not ok:
        st.error(event)
        return
    ok, registrations = api_get(f"/events/{event_id}/registrations")
    if not ok:
        st.error(registrations)
        return

    st.markdown(f"## Registrations: {event['title']}")
    st.caption(f"{event['college_name']} · {format_date(event['event_date'])}")

    registered = sum(r["status"] == "registered" for r in registrations)
    is_paid_event = float(event["registration_fee"] or 0) > 0
    collected = sum(
        r["amount_paid"] for r in registrations
        if r["status"] == "registered" and r["payment_status"] == "paid"
    )

    cards = st.columns(4 if is_paid_event else 3)
    cards[0].markdown(stat_card("Registered", registered), unsafe_allow_html=True)
    cards[1].markdown(stat_card("Cancelled", len(registrations) - registered), unsafe_allow_html=True)
    cards[2].markdown(
        stat_card("Seats left", f"{event['seats_available']} / {event['capacity']}"),
        unsafe_allow_html=True,
    )
    if is_paid_event:
        cards[3].markdown(
            stat_card("Collected (demo)", f"₹{collected:,.0f}"), unsafe_allow_html=True
        )
    st.write("")

    if not registrations:
        st.markdown('<div class="ef-empty">No students have registered yet.</div>', unsafe_allow_html=True)
        return

    rows = [
        {
            "Student": r["student_name"],
            "Email": r["student_email"],
            "College": r["student_college"] or "-",
            "Phone": r["student_phone"] or "-",
            "Registered on": local_datetime_text(r["registration_date"]),
            "Status": r["status"].title(),
            "Amount paid": f"₹{r['amount_paid']:,.0f}",
            "Payment": PAYMENT_LABELS.get(r["payment_status"], r["payment_status"]),
            "Receipt": r["payment_reference"] or "-",
        }
        for r in registrations
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download CSV",
        data=_to_csv(rows),
        file_name=f"registrations_event_{event_id}.csv",
        mime="text/csv",
    )