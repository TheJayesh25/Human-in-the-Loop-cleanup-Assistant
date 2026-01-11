import webbrowser
import time
from datetime import datetime, timezone

from workflow.engine import get_current_request
from workflow.session import SessionState

MIN_SECONDS_BETWEEN_OPENS = 8

def _can_open(last_opened_at):
    if last_opened_at is None:
        return True

    elapsed = (
        datetime.now(timezone.utc) - last_opened_at
    ).total_seconds()

    return elapsed >= MIN_SECONDS_BETWEEN_OPENS


def open_current_profile(session: SessionState) -> bool:
    if session is None:
        return False

    request = get_current_request(session)
    if request is None:
        return False

    if not _can_open(request.last_opened_at):
        return False

    url = f"https://www.instagram.com/{request.username}"

    # Open the browser tab (do NOT trust return value)
    webbrowser.open_new_tab(url)

    # Record intent immediately
    now = datetime.now(timezone.utc)
    request.last_opened_at = now
    session.last_updated_at = now

    return True

