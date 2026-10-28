"""Organizer page: create or edit an event, and manage My Events."""
from datetime import date, datetime, time, timedelta
from html import escape

import streamlit as st

from components.event_card import fee_label, format_date
from services.api_client import api_get, api_send, image_url
from services.session import current_user

EVENT_TYPES = [
    "Workshop", "Hackathon", "Seminar", "Technical",
    "Cultural", "Sports", "Competition", "Other",
]
NEW_COLLEGE = "➕ Other (add new college)"


# ---------- Callbacks (run before the page redraws) ----------

def _start_edit(event: dict) -> None:
    st.session_state["editing_event"] = event
    st.session_state["goto_tab"] = "Create Event"


def _cancel_edit() -> None:
    st.session_state["editing_event"] = None
    st.session_state["form_version"] = st.session_state.get("form_version", 0) + 1
    st.session_state["goto_tab"] = "My Events"


def _view_event(event_id: int) -> None:
    st.session_state["selected_event_id"] = event_id
    st.session_state["details_back"] = "Create Event"
    st.session_state["goto_tab"] = "My Events"
    st.session_state["page"] = "Event Details"

def _view_registrations(event_id: int) -> None:
    st.session_state["selected_event_id"] = event_id
    st.session_state["goto_tab"] = "My Events"
    st.session_state["page"] = "Event Registrations"

def _ai_fill(fid: str, kind: str) -> None:
    """Runs BEFORE the page redraws, so it may set the text box's value."""
    ss = st.session_state
    title = ss.get(f"{fid}_title", "").strip()
    audience = ss.get(f"{fid}_audience", "").strip()
    if len(title) < 3 or len(audience) < 2:
        ss["ai_msg"] = ("error", "Enter the event name and the target audience first.")
        return

    payload = {
        "title": title,
        "event_type": ss.get(f"{fid}_type", "Other"),
        "audience": audience,
        "duration": ss.get(f"{fid}_duration", "").strip() or None,
    }
    ok, result = api_send("POST", f"/ai/generate-{kind}", json=payload, timeout=60)
    if ok:
        ss[f"{fid}_{kind}"] = result["text"]  # fills the box; the organizer can edit it
        ss["ai_msg"] = ("success", f"AI {kind} added. Please review and edit it before publishing.")
    else:
        ss["ai_msg"] = ("error", result)    

def _ask_delete(event_id: int) -> None:
    st.session_state["confirm_delete"] = event_id


def _cancel_delete() -> None:
    st.session_state["confirm_delete"] = None


# ---------- Page ----------

def render_create_event() -> None:
    if current_user()["role"] != "organizer":
        st.error("Only event organizers can create events.")
        return

    # A widget's value can't be changed after it is drawn, so tab switches are
    # requested with 'goto_tab' and applied here, before the radio is drawn.
    if "goto_tab" in st.session_state:
        st.session_state["org_tab"] = st.session_state.pop("goto_tab")
    st.session_state.setdefault("org_tab", "Create Event")

    st.markdown("## Create Event")
    st.radio(
        "Section", ["Create Event", "My Events"],
        key="org_tab", horizontal=True, label_visibility="collapsed",
    )

    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)

    if st.session_state["org_tab"] == "My Events":
        _render_my_events()
    else:
        _render_form()


# ---------- Create / edit form ----------

def _render_form() -> None:
    editing = st.session_state.get("editing_event")
    ev = editing or {}
    version = st.session_state.setdefault("form_version", 0)
    fid = f"ce_{ev.get('id', 'new')}_{version}"  # unique widget keys per form

    ok, colleges = api_get("/colleges")
    if not ok:
        st.error(colleges)
        return
    college_names = [c["name"] for c in colleges]
    college_ids = {c["name"]: c["id"] for c in colleges}

    if editing:
        st.info(f"✏️ Editing: {ev['title']}")

    today = date.today()
    default_date = datetime.fromisoformat(ev["event_date"]).date() if ev else today + timedelta(days=14)

    # --- Basic information ---
    with st.container(border=True):
        st.markdown("#### Basic Information")
        title = st.text_input("Event name", value=ev.get("title", ""), key=f"{fid}_title",
                              placeholder="e.g. AI & Machine Learning Workshop")
        options = college_names + [NEW_COLLEGE]
        index = college_names.index(ev["college_name"]) if ev.get("college_name") in college_names else 0
        college_choice = st.selectbox("College", options, index=index, key=f"{fid}_college")
        new_college = ""
        if college_choice == NEW_COLLEGE:
            new_college = st.text_input("New college name", key=f"{fid}_newcollege")
        type_index = EVENT_TYPES.index(ev["event_type"]) if ev.get("event_type") in EVENT_TYPES else 0
        event_type = st.selectbox("Event type", EVENT_TYPES, index=type_index, key=f"{fid}_type")
        
        a1, a2 = st.columns(2)
        a1.text_input("Target audience (used by AI)", key=f"{fid}_audience",
                      placeholder="e.g. Engineering students")
        a2.text_input("Duration (used by AI)", key=f"{fid}_duration",
                      placeholder="e.g. One day")

        description = st.text_area("Event description", value=ev.get("description") or "",
                                   height=160, key=f"{fid}_description")
        st.button("✨ Generate description with AI", key=f"{fid}_ai_description",
                  on_click=_ai_fill, args=(fid, "description"))

        highlights = st.text_area("Event highlights (one per line)", value=ev.get("highlights") or "",
                                  height=110, key=f"{fid}_highlights")
        st.button("✨ Generate highlights with AI", key=f"{fid}_ai_highlights",
                  on_click=_ai_fill, args=(fid, "highlights"))

        ai_msg = st.session_state.pop("ai_msg", None)
        if ai_msg:
            (st.error if ai_msg[0] == "error" else st.success)(ai_msg[1])

    # --- Schedule ---
    with st.container(border=True):
        st.markdown("#### Schedule")
        c1, c2, c3 = st.columns(3)
        event_date = c1.date_input("Event date", value=default_date,
                                   min_value=min(today, default_date), key=f"{fid}_date")
        start_time = c2.time_input("Start time", value=_parse_time(ev.get("start_time"), time(10, 0)),
                                   key=f"{fid}_start")
        end_time = c3.time_input("End time", value=_parse_time(ev.get("end_time"), time(16, 0)),
                                 key=f"{fid}_end")

    # --- Location ---
    with st.container(border=True):
        st.markdown("#### Location")
        c1, c2 = st.columns(2)
        venue = c1.text_input("Venue", value=ev.get("venue", ""), key=f"{fid}_venue",
                              placeholder="e.g. Main Auditorium")
        city = c2.text_input("City", value=ev.get("city", ""), key=f"{fid}_city",
                             placeholder="e.g. Pune")

    # --- Registration ---
    with st.container(border=True):
        st.markdown("#### Registration")
        c1, c2 = st.columns(2)
        capacity = c1.number_input("Maximum capacity", min_value=1, max_value=100000,
                                   value=int(ev.get("capacity", 100)), step=10, key=f"{fid}_capacity")
        fee = c2.number_input("Registration fee (₹, 0 = free)", min_value=0,
                              value=int(ev.get("registration_fee", 0)), step=50, key=f"{fid}_fee")
        if editing:
            st.caption(f"{ev['registered_count']} students have already registered.")

        has_deadline = st.checkbox(
            "Set a registration deadline",
            value=bool(ev.get("registration_deadline")) or not editing,
            key=f"{fid}_hasdeadline",
        )
        deadline_date = None
        if has_deadline:
            if ev.get("registration_deadline"):
                default_deadline = datetime.fromisoformat(ev["registration_deadline"]).date()
            else:
                default_deadline = event_date - timedelta(days=1)
            default_deadline = min(default_deadline, event_date)
            deadline_date = st.date_input("Registration deadline", value=default_deadline,
                                          max_value=event_date, key=f"{fid}_deadline")

    # --- Image ---
    with st.container(border=True):
        st.markdown("#### Event Image")
        if ev.get("image_path"):
            st.image(image_url(ev["image_path"]), width=260)
            st.caption("Current image. Upload a new one to replace it.")
        image = st.file_uploader("Upload an image (JPG, PNG or WEBP, max 2 MB)",
                                 type=["jpg", "jpeg", "png", "webp"], key=f"{fid}_image")

    # --- Buttons ---
    b1, b2, b3 = st.columns(3)
    save_draft = b1.button("Save Draft", use_container_width=True, key=f"{fid}_draft")
    publish = b2.button("Publish Event", type="primary", use_container_width=True, key=f"{fid}_publish")
    if editing:
        b3.button("Cancel editing", use_container_width=True, on_click=_cancel_edit, key=f"{fid}_cancel")

    if not (save_draft or publish):
        return

    # --- Validation (friendly messages; the backend checks again) ---
    new_college = new_college.strip()
    if len(title.strip()) < 3:
        st.error("Please enter an event name (at least 3 characters).")
    elif college_choice == NEW_COLLEGE and len(new_college) < 2:
        st.error("Please enter the new college name.")
    elif not venue.strip() or not city.strip():
        st.error("Please enter both the venue and the city.")
    elif end_time <= start_time:
        st.error("End time must be after the start time.")
    elif publish and not description.strip():
        st.error("Please add a description before publishing.")
    else:
        payload = {
            "title": title.strip(),
            "description": description.strip(),
            "highlights": highlights.strip(),
            "event_type": event_type,
            "college_id": None if college_choice == NEW_COLLEGE else college_ids[college_choice],
            "new_college_name": new_college or None,
            "event_date": event_date.isoformat(),
            "start_time": start_time.strftime("%H:%M:%S"),
            "end_time": end_time.strftime("%H:%M:%S"),
            "venue": venue.strip(),
            "city": city.strip(),
            "capacity": int(capacity),
            "registration_fee": float(fee),
            "registration_deadline": (
                datetime.combine(deadline_date, time(23, 59)).isoformat() if deadline_date else None
            ),
            "status": "published" if publish else "draft",
        }
        _submit(payload, editing, image)


def _submit(payload: dict, editing: dict | None, image) -> None:
    if editing:
        ok, result = api_send("PUT", f"/events/{editing['id']}", json=payload)
    else:
        ok, result = api_send("POST", "/events", json=payload)
    if not ok:
        st.error(result)
        return

    message = "Event published! Students can now find it in Discover Events." \
        if payload["status"] == "published" else "Draft saved. Publish it from My Events when ready."

    if image is not None:
        files = {"file": (image.name, image.getvalue(), image.type)}
        img_ok, img_result = api_send("POST", f"/events/{result['id']}/image", files=files)
        if not img_ok:
            message += f" (The event was saved, but the image failed: {img_result})"

    st.session_state["editing_event"] = None
    st.session_state["form_version"] = st.session_state.get("form_version", 0) + 1  # blank form next time
    st.session_state["flash"] = message
    st.session_state["goto_tab"] = "My Events"
    st.rerun()


def _parse_time(value: str | None, fallback: time) -> time:
    return time.fromisoformat(value) if value else fallback


# ---------- My Events ----------

def _render_my_events() -> None:
    ok, events = api_get("/my-events")
    if not ok:
        st.error(events)
        return
    if not events:
        st.markdown(
            '<div class="ef-empty">You have not created any events yet. Use the Create Event section.</div>',
            unsafe_allow_html=True,
        )
        return

    st.caption(f"{len(events)} event{'s' if len(events) != 1 else ''}")
    for event in events:
        _event_row(event)


def _registration_status(event: dict) -> str:
    if event["seats_available"] == 0:
        return "Full"
    deadline = event["registration_deadline"]
    if deadline and datetime.fromisoformat(deadline) < datetime.now():
        return "Closed"
    return "Open"


def _event_row(event: dict) -> None:
    with st.container(border=True):
        left, right = st.columns([3, 2])
        left.markdown(
            f'<div class="ef-row-title">{escape(event["title"])}'
            f'<span class="ef-badge {event["status"]}">{event["status"].title()}</span></div>'
            f'<div class="ef-row-sub">🏛️ {escape(event["college_name"])} · 📅 {format_date(event["event_date"])} '
            f'· {fee_label(event["registration_fee"])}</div>',
            unsafe_allow_html=True,
        )
        right.markdown(
            f'<div class="ef-row-sub"><b>{event["registered_count"]}</b> registered · '
            f'<b>{event["seats_available"]}</b> seats left of {event["capacity"]}<br>'
            f'Registration: <b>{_registration_status(event)}</b></div>',
            unsafe_allow_html=True,
        )

        b1, b2, b3, b4, b5 = st.columns(5)
        b1.button("View", key=f"view_{event['id']}", use_container_width=True,
                  on_click=_view_event, args=(event["id"],))
        b2.button("Edit", key=f"edit_{event['id']}", use_container_width=True,
                  on_click=_start_edit, args=(event,))

        publish_label = "Unpublish" if event["status"] == "published" else "Publish"
        if b3.button(publish_label, key=f"toggle_{event['id']}", use_container_width=True):
            new_status = "draft" if event["status"] == "published" else "published"
            ok, result = api_send("PATCH", f"/events/{event['id']}/status", json={"status": new_status})
            if ok:
                st.rerun()
            else:
                st.error(result)

        b4.button("Registrations", key=f"regs_{event['id']}", use_container_width=True,
                  on_click=_view_registrations, args=(event["id"],))

        b5.button("Delete", key=f"del_{event['id']}", use_container_width=True,
                  on_click=_ask_delete, args=(event["id"],))

        if st.session_state.get("confirm_delete") == event["id"]:
            st.warning(
                f"Delete \"{event['title']}\"? Its {event['registered_count']} registration(s) "
                "will be removed too. This cannot be undone."
            )
            y, n = st.columns(2)
            if y.button("Yes, delete", key=f"yes_{event['id']}", type="primary", use_container_width=True):
                ok, result = api_send("DELETE", f"/events/{event['id']}")
                st.session_state["confirm_delete"] = None
                if ok:
                    st.session_state["flash"] = "Event deleted."
                    st.rerun()
                else:
                    st.error(result)
            n.button("Cancel", key=f"no_{event['id']}", use_container_width=True, on_click=_cancel_delete)