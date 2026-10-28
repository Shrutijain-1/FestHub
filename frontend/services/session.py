"""Stores login state in Streamlit's session_state."""
import streamlit as st


def save_session(token: str, user: dict) -> None:
    st.session_state["token"] = token
    st.session_state["user"] = user


def clear_session() -> None:
    st.session_state.pop("token", None)
    st.session_state.pop("user", None)


def is_logged_in() -> bool:
    return "token" in st.session_state


def current_user() -> dict | None:
    return st.session_state.get("user")


def get_token() -> str | None:
    return st.session_state.get("token")