"""Student page: every event the student registered for."""
from html import escape

import streamlit as st

from components.event_card import fee_label, format_date, format_time
from services.api_client import api_get, api_send
from services.session import current_user


def _view(event_id: int) -> None:
    st.session_state["selected_event_id"] = event_id
    st.session_state["details_back"] = "My Registrations"
    st.session_state["page"] = "Event Details"


def _ask_cancel(registration_id: int) -> None:
    st.session_state["confirm_cancel"] = registration_id


def _keep() -> None:
    st.session_state["confirm_cancel"] = None


def render_my_registrations() -> None:
    if current_user()["role"] != "student":
        st.error("Only students have registrations.")
        return

    st.markdown("## My Registrations")

    flash = st.session_state.pop("mine_flash", None)
    if flash:
        st.success(flash)

    ok, registrations = api_get("/my-registrations")
    if not ok:
        st.error(registrations)
        return
    if not registrations:
        st.markdown(
            '<div class="ef-empty">You have not registered for any events yet. '
            "Open Discover Events to find one.</div>",
            unsafe_allow_html=True,
        )
        return

    active = sorted(
        (r for r in registrations if r["status"] == "registered"),
        key=lambda r: r["event_date"],
    )
    cancelled = [r for r in registrations if r["status"] == "cancelled"]
    st.caption(f"{len(active)} active · {len(cancelled)} cancelled")

    for registration in active + cancelled:
        _registration_row(registration)


def _payment_lines(reg: dict) -> str:
    """One extra line about the payment or refund, or nothing for free events."""
    if reg["payment_status"] == "paid":
        return (
            f'<div class="ef-row-sub">💳 Paid {fee_label(reg["amount_paid"])} via '
            f'{escape(reg["payment_method"] or "-")} · Receipt {escape(reg["payment_reference"] or "-")}</div>'
        )
    if reg["payment_status"] == "refund_initiated":
        return (
            f'<div class="ef-row-sub">↩️ Refund of {fee_label(reg["amount_paid"])} initiated · '
            f'Ref {escape(reg["refund_reference"] or "-")}</div>'
        )
    return ""


def _registration_row(reg: dict) -> None:
    with st.container(border=True):
        st.markdown(
            f'<div class="ef-row-title">{escape(reg["event_title"])}'
            f'<span class="ef-badge {reg["status"]}">{reg["status"].title()}</span></div>'
            f'<div class="ef-row-sub">🏛️ {escape(reg["college_name"])} · '
            f'📅 {format_date(reg["event_date"])} · ⏰ {format_time(reg["start_time"])}</div>'
            f'<div class="ef-row-sub">📍 {escape(reg["venue"])}, {escape(reg["city"])}</div>'
            + _payment_lines(reg),
            unsafe_allow_html=True,
        )
        if reg.get("refund_message"):
            st.caption(reg["refund_message"])

        b1, b2, _ = st.columns([1, 1.4, 2])
        b1.button("View Details", key=f"view_{reg['id']}", use_container_width=True,
                  on_click=_view, args=(reg["event_id"],))
        if reg["status"] == "registered":
            b2.button("Cancel Registration", key=f"cancel_{reg['id']}", use_container_width=True,
                      on_click=_ask_cancel, args=(reg["id"],))

        if st.session_state.get("confirm_cancel") == reg["id"]:
            warning = f"Cancel your registration for \"{reg['event_title']}\"? Your seat will be released."
            if reg["payment_status"] == "paid":
                warning += (
                    f" Your payment of {fee_label(reg['amount_paid'])} will be refunded "
                    "to your account within 24 hours."
                )
            st.warning(warning)
            y, n = st.columns(2)
            if y.button("Yes, cancel", key=f"yes_{reg['id']}", type="primary", use_container_width=True):
                ok, result = api_send("DELETE", f"/registrations/{reg['id']}")
                st.session_state["confirm_cancel"] = None
                if ok:
                    message = "Registration cancelled."
                    if result and result.get("refund_message"):
                        message += " " + result["refund_message"]
                    st.session_state["mine_flash"] = message
                    st.rerun()
                else:
                    st.error(result)
            n.button("Keep it", key=f"no_{reg['id']}", use_container_width=True, on_click=_keep)