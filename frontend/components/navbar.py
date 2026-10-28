"""Top navigation bar. Items depend on the user's role."""
import streamlit as st

from services.session import clear_session, current_user

NAV_ITEMS = {
    "student": ["Home", "Discover Events", "My Registrations", "AI Assistant", "Profile"],
    "organizer": ["Home", "Discover Events", "Create Event", "AI Assistant", "Profile"],
}


def _go(page: str) -> None:
    st.session_state["page"] = page


def render_navbar() -> None:
    items = NAV_ITEMS[current_user()["role"]]
    active = st.session_state.get("page", "Home")

    with st.container(key="navbar"):
        cols = st.columns([1.5] + [1.4] * len(items) + [0.9])
        cols[0].markdown('<div class="ef-brand">Fest<span>Hub</span></div>', unsafe_allow_html=True)
        for col, label in zip(cols[1:-1], items):
            col.button(
                label,
                key=f"nav_{label}",
                type="primary" if label == active else "secondary",
                use_container_width=True,
                on_click=_go,
                args=(label,),
            )
        cols[-1].button("Logout", key="nav_logout", use_container_width=True, on_click=_logout)


def _logout() -> None:
    clear_session()
    st.session_state["page"] = "Home"
    st.session_state["view"] = "login"