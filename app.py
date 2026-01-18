import streamlit as st
import uuid
from pathlib import Path
from datetime import datetime, timezone

from workflow.parser import parse_pending_follow_requests
from workflow.session import initialize_session, save_session, load_session
from workflow.engine import (
    get_current_request,
    mark_completed,
    mark_skipped,
    has_more,
)
from workflow.browser import get_current_profile_url

# --------------------------------------------------
# Streamlit config
# --------------------------------------------------
st.set_page_config(
    page_title="Instagram Pending Request Cleanup",
    layout="centered",
)

SESSION_FILE = Path("session_state.json")

# --------------------------------------------------
# Initialize Streamlit state
# --------------------------------------------------
if "session" not in st.session_state:
    st.session_state.session = None

if "auto_advance" not in st.session_state:
    st.session_state.auto_advance = False

if "mode_selected" not in st.session_state:
    st.session_state.mode_selected = False

# App phases: INIT | RUNNING | STOPPED
if "app_phase" not in st.session_state:
    st.session_state.app_phase = "INIT"

# Resettable uploader
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())

st.title("Instagram Pending Follow Request Cleanup")

# --------------------------------------------------
# STOPPED SCREEN
# --------------------------------------------------
if st.session_state.app_phase == "STOPPED":
    st.subheader("Session paused")

    st.write(
        "Your progress has been saved. "
        "You can resume from where you left off or reset the session."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Resume Session"):
            st.session_state.session = load_session(SESSION_FILE)
            st.session_state.app_phase = "RUNNING"
            st.rerun()

    with col2:
        if st.button("Reset Session"):
            SESSION_FILE.unlink(missing_ok=True)
            st.session_state.session = None
            st.session_state.mode_selected = False
            st.session_state.auto_advance = False
            st.session_state.app_phase = "INIT"
            st.session_state.uploader_key = str(uuid.uuid4())
            st.rerun()

    st.stop()

# --------------------------------------------------
# Upload (INIT only)
# --------------------------------------------------
uploaded_file = None
if st.session_state.app_phase == "INIT":
    uploaded_file = st.file_uploader(
        "Upload pending_follow_requests.json",
        type=["json"],
        key=st.session_state.uploader_key,
    )

if uploaded_file and st.session_state.app_phase == "INIT":
    temp_path = Path("uploaded_pending_requests.json")
    temp_path.write_bytes(uploaded_file.read())

    pending_requests = parse_pending_follow_requests(temp_path)
    st.session_state.session = initialize_session(
        pending_requests,
        session_id=str(uuid.uuid4()),
    )

    st.session_state.app_phase = "RUNNING"
    st.rerun()

# --------------------------------------------------
# HARD GUARD
# --------------------------------------------------
session = st.session_state.session
if session is None:
    st.info("Upload your Instagram pending_follow_requests.json file to begin.")
    st.stop()

# --------------------------------------------------
# Sidebar (Progress View)
# --------------------------------------------------
with st.sidebar:
    st.header("Progress")

    completed = [u for u, s in session.requests.items() if s.status == "completed"]
    skipped = [u for u, s in session.requests.items() if s.status == "skipped"]
    pending = [u for u, s in session.requests.items() if s.status == "pending"]

    st.write(f"✅ Completed: {len(completed)}")
    st.write(f"⏭ Skipped: {len(skipped)}")
    st.write(f"⏳ Pending: {len(pending)}")

    st.divider()
    st.subheader("Queue")

    for idx, username in enumerate(session.order):
        state = session.requests[username]

        if idx == session.current_index:
            prefix = "👉"
        elif state.status == "completed":
            prefix = "✅"
        elif state.status == "skipped":
            prefix = "⏭"
        else:
            prefix = "•"

        st.text(f"{prefix} @{username}")

# --------------------------------------------------
# MODE SELECTION
# --------------------------------------------------
if not st.session_state.mode_selected:
    st.subheader("Choose Workflow Mode")

    st.write(
        "You can either manually open each profile, or let the app "
        "automatically advance after confirmation."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Manual Mode"):
            st.session_state.auto_advance = False
            st.session_state.mode_selected = True
            st.rerun()

    with col2:
        if st.button("Guided Mode"):
            st.session_state.auto_advance = True
            st.session_state.mode_selected = True
            st.rerun()

    st.stop()

# --------------------------------------------------
# Completion Check
# --------------------------------------------------
if not has_more(session):
    st.success("All pending follow requests processed.")
    st.stop()

# --------------------------------------------------
# Active Request UI
# --------------------------------------------------
req = get_current_request(session)

st.subheader("Current Request")
st.write(f"**Username:** @{req.username}")

opened = req.last_opened_at is not None

if opened:
    st.success("Profile confirmed as opened. You may proceed.")
else:
    st.info("Open the profile and confirm before continuing.")

# --------------------------------------------------
# Open Profile (Human-confirmed)
# --------------------------------------------------
profile_url = get_current_profile_url(session)

if profile_url:
    st.link_button(
        "Open Instagram Profile (New Tab)",
        profile_url,
        help="You must already be logged in to Instagram.",
    )

    if st.button("I've opened this profile"):
        now = datetime.now(timezone.utc)
        req.last_opened_at = now
        session.last_updated_at = now
        save_session(session, SESSION_FILE)
        st.rerun()
else:
    st.button("Open Instagram Profile", disabled=True)

# --------------------------------------------------
# Action Buttons (STRICTLY ENFORCED)
# --------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("Mark as Completed", disabled=not opened):
        mark_completed(session)
        save_session(session, SESSION_FILE)
        st.rerun()

with col2:
    if st.button("Skip", disabled=not opened):
        mark_skipped(session)
        save_session(session, SESSION_FILE)
        st.rerun()

# --------------------------------------------------
# Stop / Save
# --------------------------------------------------
st.divider()

if st.button("Stop for now"):
    save_session(session, SESSION_FILE)
    st.session_state.session = None
    st.session_state.app_phase = "STOPPED"
    st.rerun()
