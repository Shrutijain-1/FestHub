"""Profile page: view details and edit name, college and phone."""
from html import escape

import streamlit as st

from services.api_client import api_send
from services.session import current_user


def render_profile() -> None:
    user = current_user()
    st.markdown("## Profile")

    flash = st.session_state.pop("profile_flash", None)
    if flash:
        st.success(flash)

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
    st.write("")

    with st.form("profile_form"):
        st.markdown("#### Edit details")
        name = st.text_input("Full name", value=user["name"])
        st.text_input("Email (cannot be changed)", value=user["email"], disabled=True)
        college = st.text_input("College", value=user.get("college") or "")
        phone = st.text_input("Phone", value=user.get("phone") or "", placeholder="10-digit number")
        saved = st.form_submit_button("Save changes", type="primary")

    if not saved:
        return

    name, college, phone = name.strip(), college.strip(), phone.strip()
    if len(name) < 2:
        st.error("Please enter your full name.")
    elif phone and not (phone.isdigit() and len(phone) == 10):
        st.error("Phone number must be exactly 10 digits.")
    else:
        ok, result = api_send(
            "PUT", "/auth/me",
            json={"name": name, "college": college or None, "phone": phone or None},
        )
        if ok:
            st.session_state["user"] = result  # the navbar and greeting use this
            st.session_state["profile_flash"] = "Profile updated."
            st.rerun()
        else:
            st.error(result)