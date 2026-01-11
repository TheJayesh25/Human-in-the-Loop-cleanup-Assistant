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


def mark_profile_opened(session: SessionState) -> bool:
    """
    Records user intent to open the current profile.
    Does NOT attempt to open a browser.
    """
    if session is None:
        return False

    request = get_current_request(session)
    if request is None:
        return False

    if not _can_open(request.last_opened_at):
        return False

    now = datetime.now(timezone.utc)
    request.last_opened_at = now
    session.last_updated_at = now

    return True
