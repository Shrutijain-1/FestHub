"""Signup screen."""
import re

import streamlit as st

from services.api_client import register_user
from services.session import save_session

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _go_login() -> None:
    st.session_state["view"] = "login"


def render_signup() -> None:
    _, center, _ = st.columns([1, 1.3, 1])
    with center:
        st.markdown(
            '<div class="ef-auth-brand"><div class="ef-brand">Fest<span>Hub</span></div>'
            '<div class="ef-tagline">Plan. Discover. Experience.</div></div>',
            unsafe_allow_html=True,
        )

        with st.form("signup_form"):
            st.markdown("### Create your account")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password", help="At least 6 characters")
            confirm = st.text_input("Confirm Password", type="password")
            role = st.selectbox("I am a", ["Student", "Event Organizer"])
            college = st.text_input("College (optional)")
            phone = st.text_input("Phone (optional)", placeholder="10-digit number")
            submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

        if submitted:
            name, email, phone = name.strip(), email.strip(), phone.strip()
            if not (name and email and password and confirm):
                st.error("Please fill in all required fields.")
            elif not EMAIL_PATTERN.match(email):
                st.error("That doesn't look like a valid email address.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif phone and not (phone.isdigit() and len(phone) == 10):
                st.error("Phone number must be exactly 10 digits.")
            else:
                role_value = "student" if role == "Student" else "organizer"
                success, data = register_user(name, email, password, role_value, college.strip(), phone)
                if success:
                    save_session(data["access_token"], data["user"])
                    st.rerun()
                else:
                    st.error(data)

        st.button("Already have an account? Login", use_container_width=True, on_click=_go_login)