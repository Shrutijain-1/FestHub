"""Forgot password (demo mode): request a code, then set a new password."""
import re

import streamlit as st

from services.api_client import api_post_public

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _go_login() -> None:
    st.session_state.pop("reset_email", None)
    st.session_state.pop("reset_demo_code", None)
    st.session_state["view"] = "login"


def _use_other_email() -> None:
    st.session_state.pop("reset_email", None)
    st.session_state.pop("reset_demo_code", None)


def render_forgot_password() -> None:
    _, center, _ = st.columns([1, 1.3, 1])
    with center:
        st.markdown(
            '<div class="ef-auth-brand"><div class="ef-brand">Fest<span>Hub</span></div>'
            '<div class="ef-tagline">Plan. Discover. Experience.</div></div>',
            unsafe_allow_html=True,
        )

        reset_email = st.session_state.get("reset_email")
        if not reset_email:
            _request_step()
        else:
            _reset_step(reset_email)

        st.button("← Back to login", use_container_width=True, on_click=_go_login)


def _request_step() -> None:
    with st.form("forgot_form"):
        st.markdown("### Reset your password")
        email = st.text_input("Email", placeholder="you@college.edu")
        submitted = st.form_submit_button("Send reset code", type="primary", use_container_width=True)

    if not submitted:
        return
    email = email.strip()
    if not EMAIL_PATTERN.match(email):
        st.error("That doesn't look like a valid email address.")
        return

    ok, data = api_post_public("/auth/forgot-password", {"email": email})
    if ok:
        st.session_state["reset_email"] = email
        st.session_state["reset_demo_code"] = data.get("demo_code")
        st.rerun()
    else:
        st.error(data)


def _reset_step(email: str) -> None:
    st.markdown("### Enter your code")
    demo_code = st.session_state.get("reset_demo_code")
    if demo_code:
        st.warning(
            f"**Demo mode:** this project has no email service, so your code is shown here: "
            f"**{demo_code}**. A real app would email it instead."
        )
    else:
        st.info(
            "If that email is registered, a code was created. This project has no email service, "
            "so the code appears in the backend terminal."
        )

    with st.form("reset_form"):
        code = st.text_input("6-digit code", max_chars=6)
        new_password = st.text_input("New password", type="password", help="At least 6 characters")
        confirm = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Reset password", type="primary", use_container_width=True)

    st.button("Use a different email", use_container_width=True, on_click=_use_other_email)

    if not submitted:
        return
    code = code.strip()
    if not (code.isdigit() and len(code) == 6):
        st.error("The code must be 6 digits.")
    elif len(new_password) < 6:
        st.error("Password must be at least 6 characters.")
    elif new_password != confirm:
        st.error("Passwords do not match.")
    else:
        ok, data = api_post_public(
            "/auth/reset-password",
            {"email": email, "code": code, "new_password": new_password},
        )
        if ok:
            st.session_state.pop("reset_email", None)
            st.session_state.pop("reset_demo_code", None)
            st.session_state["login_flash"] = "Password updated. Please log in with your new password."
            st.session_state["view"] = "login"
            st.rerun()
        else:
            st.error(data)