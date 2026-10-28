"""AI Assistant page: planning tools for organizers, ideas and chat for everyone."""
import streamlit as st

from services.api_client import api_send
from services.session import current_user

EVENT_TYPES = [
    "Workshop", "Hackathon", "Seminar", "Technical",
    "Cultural", "Sports", "Competition", "Other",
]


def _run_tool(key: str, path: str, payload: dict) -> None:
    with st.spinner("Gemini is working on it..."):
        ok, result = api_send("POST", path, json=payload, timeout=60)
    if ok:
        st.session_state[f"ai_out_{key}"] = result["text"]
    else:
        st.session_state.pop(f"ai_out_{key}", None)
        st.error(result)


def _show(key: str, label: str, as_text: bool = True) -> None:
    text = st.session_state.get(f"ai_out_{key}")
    if not text:
        return
    st.markdown("##### Result")
    if as_text:
        st.text_area(f"{label}: edit or copy", value=text, height=320)
    else:
        with st.container(border=True):
            st.markdown(text)


def _brief_fields(prefix: str) -> dict:
    c1, c2 = st.columns(2)
    title = c1.text_input("Event name", key=f"{prefix}_title",
                          placeholder="AI and Machine Learning Workshop")
    event_type = c2.selectbox("Event type", EVENT_TYPES, key=f"{prefix}_type")
    c3, c4 = st.columns(2)
    audience = c3.text_input("Target audience", key=f"{prefix}_aud",
                             placeholder="Engineering students")
    duration = c4.text_input("Duration", key=f"{prefix}_dur", placeholder="One day")
    return {
        "title": title.strip(), "event_type": event_type,
        "audience": audience.strip(), "duration": duration.strip() or None,
    }


def _is_valid(brief: dict) -> bool:
    if len(brief["title"]) < 3 or len(brief["audience"]) < 2:
        st.error("Please enter the event name and the target audience.")
        return False
    return True


# ---------- Organizer tools ----------

def _description_tab() -> None:
    with st.form("ai_description_form"):
        brief = _brief_fields("desc")
        notes = st.text_input("Anything to mention? (optional)", key="desc_notes")
        go = st.form_submit_button("✨ Generate description", type="primary")
    if go and _is_valid(brief):
        _run_tool("desc", "/ai/generate-description", {**brief, "notes": notes.strip() or None})
    _show("desc", "Description")


def _schedule_tab() -> None:
    with st.form("ai_schedule_form"):
        brief = _brief_fields("sched")
        go = st.form_submit_button("✨ Generate schedule", type="primary")
    if go and _is_valid(brief):
        _run_tool("sched", "/ai/generate-schedule", brief)
    _show("sched", "Schedule")


def _invitation_tab() -> None:
    with st.form("ai_invitation_form"):
        brief = _brief_fields("inv")
        c1, c2, c3 = st.columns(3)
        date_text = c1.text_input("Date (optional)", key="inv_date", placeholder="12 Nov 2026")
        venue = c2.text_input("Venue (optional)", key="inv_venue", placeholder="Main Auditorium")
        channel = c3.selectbox("Channel", ["WhatsApp", "Email", "Social media"], key="inv_channel")
        go = st.form_submit_button("✨ Generate invitation", type="primary")
    if go and _is_valid(brief):
        channel_value = {"WhatsApp": "whatsapp", "Email": "email", "Social media": "social"}[channel]
        _run_tool("inv", "/ai/generate-invitation", {
            **brief, "channel": channel_value,
            "date_text": date_text.strip() or None, "venue": venue.strip() or None,
        })
    _show("inv", "Invitation")


def _checklist_tab() -> None:
    with st.form("ai_checklist_form"):
        brief = _brief_fields("check")
        attendees = st.number_input("Expected attendees", min_value=1, max_value=100000,
                                    value=100, step=10, key="check_attendees")
        go = st.form_submit_button("✨ Generate checklist", type="primary")
    if go and _is_valid(brief):
        _run_tool("check", "/ai/generate-checklist", {**brief, "attendees": int(attendees)})
    _show("check", "Checklist", as_text=False)


# ---------- Tools for everyone ----------

def _ideas_tab() -> None:
    with st.form("ai_ideas_form"):
        prompt = st.text_area(
            "What kind of events do you need ideas for?", key="ideas_prompt", height=100,
            placeholder="Suggest technical events for second-year engineering students.",
        )
        go = st.form_submit_button("✨ Get ideas", type="primary")
    if go:
        if len(prompt.strip()) < 5:
            st.error("Please describe what you need (at least 5 characters).")
        else:
            _run_tool("ideas", "/ai/event-ideas", {"prompt": prompt.strip()})
    _show("ideas", "Ideas", as_text=False)


def _chat_tab() -> None:
    history = st.session_state.setdefault("ai_chat", [])
    if not history:
        st.caption("Try: \"What should I arrange for a 200-person technical workshop?\"")
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask about planning an event...")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ok, result = api_send(
                    "POST", "/ai/chat", timeout=60,
                    json={"message": prompt, "history": history[-10:]},
                )
            if ok:
                st.markdown(result["text"])
                history.append({"role": "user", "content": prompt})
                history.append({"role": "assistant", "content": result["text"]})
            else:
                st.error(result)

    if history and st.button("Clear chat"):
        st.session_state["ai_chat"] = []
        st.rerun()


def render_ai_assistant() -> None:
    st.markdown("## AI Assistant")
    st.markdown(
        '<div class="ef-tagline">Powered by Gemini. AI can make mistakes, so always review the result.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    is_organizer = current_user()["role"] == "organizer"
    names = (["Description", "Schedule", "Invitation", "Checklist"] if is_organizer else [])
    names += ["Event Ideas", "Chat"]
    tabs = dict(zip(names, st.tabs(names)))

    if is_organizer:
        with tabs["Description"]:
            _description_tab()
        with tabs["Schedule"]:
            _schedule_tab()
        with tabs["Invitation"]:
            _invitation_tab()
        with tabs["Checklist"]:
            _checklist_tab()
    with tabs["Event Ideas"]:
        _ideas_tab()
    with tabs["Chat"]:
        _chat_tab()