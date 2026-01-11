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

st.title("Instagram Pending Follow Request Cleanup")

# --------------------------------------------------
# Upload / Resume Logic
# --------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload pending_follow_requests.json",
    type=["json"],
)

if uploaded_file and st.session_state.session is None:
    temp_path = Path("uploaded_pending_requests.json")
    temp_path.write_bytes(uploaded_file.read())

    if SESSION_FILE.exists():
        st.info("Existing session found. Resuming progress.")
        st.session_state.session = load_session(SESSION_FILE)
    else:
        pending_requests = parse_pending_follow_requests(temp_path)
        st.session_state.session = initialize_session(
            pending_requests,
            session_id=str(uuid.uuid4()),
        )

# --------------------------------------------------
# HARD GUARD — no workflow without session
# --------------------------------------------------
session = st.session_state.session

if session is None:
    st.info("Upload your Instagram pending_follow_requests.json file to begin.")
    st.stop()

# --------------------------------------------------
# MODE SELECTION (ONCE PER SESSION LOAD)
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
# Completion Check
# --------------------------------------------------
if not has_more(session):
    st.success("All pending follow requests processed.")
    if st.button("Clear session and start fresh"):
        SESSION_FILE.unlink(missing_ok=True)
        st.session_state.session = None
        st.session_state.mode_selected = False
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
    if st.button(
        "Mark as Completed",
        disabled=not opened,
    ):
        success = mark_completed(session)
        if not success:
            st.warning("You must open the Instagram profile first.")
        save_session(session, SESSION_FILE)

        # AUTO-ADVANCE (GUIDED MODE)
        if st.session_state.auto_advance and has_more(session):
            open_current_profile(session)
            save_session(session, SESSION_FILE)

        st.rerun()

with col2:
    if st.button(
        "Skip",
        disabled=not opened,
    ):
        success = mark_skipped(session)
        if not success:
            st.warning("You must open the Instagram profile first.")
        save_session(session, SESSION_FILE)

        # AUTO-ADVANCE (GUIDED MODE)
        if st.session_state.auto_advance and has_more(session):
            open_current_profile(session)
            save_session(session, SESSION_FILE)

        st.rerun()

# --------------------------------------------------
# Stop / Save
# --------------------------------------------------
st.divider()

if st.button("Stop for now"):
    save_session(session, SESSION_FILE)
    st.info("Progress saved. You can safely resume later.")
    st.stop()
