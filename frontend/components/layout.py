"""Loads the custom CSS file into Streamlit."""
from pathlib import Path

import streamlit as st

CSS_PATH = Path(__file__).resolve().parent.parent / "styles" / "main.css"


def load_css() -> None:
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)