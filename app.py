import streamlit as st
import uuid
from pathlib import Path

from workflow.parser import parse_pending_follow_requests
from workflow.session import initialize_session, save_session, load_session
from workflow.engine import (
    get_current_request,
    mark_completed,
    mark_skipped,
    has_more,
)
from workflow.browser import open_current_profile

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

# File uploader must be resettable
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())

st.title("Instagram Pending Follow Request Cleanup")

# --------------------------------------------------
# STOPPED SCREEN (renders first if active)
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
# Upload (ONLY in INIT phase)
# --------------------------------------------------
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
# HARD GUARD — no workflow without session
# --------------------------------------------------
session = st.session_state.session

if session is None:
    st.info("Upload your Instagram pending_follow_requests.json file to begin.")
    st.stop()

# --------------------------------------------------
# Sidebar (Progress View) — MUST be here
# --------------------------------------------------
with st.sidebar:
    st.header("Progress")

    completed = [
        u for u, s in session.requests.items() if s.status == "completed"
    ]
    skipped = [
        u for u, s in session.requests.items() if s.status == "skipped"
    ]
    pending = [
        u for u, s in session.requests.items() if s.status == "pending"
    ]

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
# MODE SELECTION (ONCE PER SESSION)
# --------------------------------------------------
if not st.session_state.mode_selected:
    st.subheader("Choose Workflow Mode")

    st.write(
        "You can either manually open each profile, or let the app "
        "automatically open the next profile after you confirm completion or skip."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Manual Mode"):
            st.session_state.auto_advance = False
            st.session_state.mode_selected = True
            st.rerun()

    with col2:
        if st.button("Guided Mode (Auto-open next)"):
            st.session_state.auto_advance = True
            st.session_state.mode_selected = True
            st.rerun()

    st.stop()

# --------------------------------------------------
# Completion Check
# --------------------------------------------------
if not has_more(session):
    st.success("All pending follow requests processed.")

    if st.button("Clear session and start fresh"):
        SESSION_FILE.unlink(missing_ok=True)
        st.session_state.session = None
        st.session_state.mode_selected = False
        st.session_state.auto_advance = False
        st.session_state.app_phase = "INIT"
        st.session_state.uploader_key = str(uuid.uuid4())
        st.rerun()

    st.stop()

# --------------------------------------------------
# Active Request UI
# --------------------------------------------------
req = get_current_request(session)

st.subheader("Current Request")
st.write(f"**Username:** @{req.username}")

opened = req.last_opened_at is not None

if opened:
    st.success("Profile opened — complete the action on Instagram, then continue.")
else:
    st.info("Open the Instagram profile to proceed.")

# --------------------------------------------------
# Open Profile
# --------------------------------------------------
if st.button("Open Instagram Profile (New Tab)"):
    opened_ok = open_current_profile(session)
    save_session(session, SESSION_FILE)

    if not opened_ok:
        st.warning("Please wait before opening again.")
    else:
        st.rerun()

# --------------------------------------------------
# Action Buttons (STRICTLY ENFORCED)
# --------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("Mark as Completed", disabled=not opened):
        mark_completed(session)
        save_session(session, SESSION_FILE)

        if st.session_state.auto_advance and has_more(session):
            open_current_profile(session)
            save_session(session, SESSION_FILE)

        st.rerun()

with col2:
    if st.button("Skip", disabled=not opened):
        mark_skipped(session)
        save_session(session, SESSION_FILE)

        if st.session_state.auto_advance and has_more(session):
            open_current_profile(session)
            save_session(session, SESSION_FILE)

        st.rerun()

# --------------------------------------------------
# Stop / Save → transition to STOPPED
# --------------------------------------------------
st.divider()

if st.button("Stop for now"):
    save_session(session, SESSION_FILE)
    st.session_state.session = None
    st.session_state.app_phase = "STOPPED"
    st.rerun()
