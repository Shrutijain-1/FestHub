"""Login screen."""
import re

import streamlit as st

from services.api_client import login_user
from services.session import save_session

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _go_signup() -> None:
    st.session_state["view"] = "signup"


def _go_forgot() -> None:
    st.session_state["view"] = "forgot"


def render_login() -> None:
    _, center, _ = st.columns([1, 1.3, 1])
    with center:
        st.markdown(
            '<div class="ef-auth-brand"><div class="ef-brand">Fest<span>Hub</span></div>'
            '<div class="ef-tagline">Plan. Discover. Experience.</div></div>',
            unsafe_allow_html=True,
        )

        flash = st.session_state.pop("login_flash", None)
        if flash:
            st.success(flash)

        with st.form("login_form"):
            st.markdown("### Welcome")
            email = st.text_input(
                "Email", placeholder="you@college.edu",
                value=st.session_state.get("remembered_email", ""),
            )
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            remember = st.checkbox("Remember me")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submitted:
            email = email.strip()
            if not email or not password:
                st.error("Please enter both your email and password.")
            elif not EMAIL_PATTERN.match(email):
                st.error("That doesn't look like a valid email address.")
            else:
                success, data = login_user(email, password)
                if success:
                    if remember:
                        st.session_state["remembered_email"] = email
                    else:
                        st.session_state.pop("remembered_email", None)
                    save_session(data["access_token"], data["user"])
                    st.rerun()
                else:
                    st.error(data)

        left, right = st.columns(2)
        left.button("Forgot password?", use_container_width=True, on_click=_go_forgot)
        right.button("Create account", use_container_width=True, on_click=_go_signup)