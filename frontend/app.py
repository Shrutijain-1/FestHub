"""Entry point of the Streamlit frontend: routes between auth screens and app pages."""
import streamlit as st

from components.layout import load_css
from components.navbar import render_navbar
from services.session import is_logged_in
from views.ai_assistant import render_ai_assistant
from views.create_event import render_create_event
from views.discover import render_discover
from views.event_details import render_event_details
from views.event_registrations import render_event_registrations
from views.forgot_password import render_forgot_password
from views.home import render_home
from views.login import render_login
from views.my_registrations import render_my_registrations
from views.profile import render_profile
from views.signup import render_signup

st.set_page_config(page_title="FestHub", page_icon="🎯", layout="wide")
load_css()

st.session_state.setdefault("view", "login")
st.session_state.setdefault("page", "Home")

if not is_logged_in():
    view = st.session_state["view"]
    if view == "signup":
        render_signup()
    elif view == "forgot":
        render_forgot_password()
    else:
        render_login()
else:
    render_navbar()
    page = st.session_state["page"]

    if page == "Home":
        render_home()
    elif page == "Discover Events":
        render_discover()
    elif page == "Event Details":
        render_event_details()
    elif page == "My Registrations":
        render_my_registrations()
    elif page == "Create Event":
        render_create_event()
    elif page == "Event Registrations":
        render_event_registrations()
    elif page == "AI Assistant":
        render_ai_assistant()
    elif page == "Profile":
        render_profile()