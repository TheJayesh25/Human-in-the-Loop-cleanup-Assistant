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


def get_current_profile_url(session: SessionState) -> str | None:
    if session is None:
        return None

    request = get_current_request(session)
    if request is None:
        return None

    if not _can_open(request.last_opened_at):
        return None

    # Record intent immediately (human will click)
    now = datetime.now(timezone.utc)
    request.last_opened_at = now
    session.last_updated_at = now

    return f"https://www.instagram.com/{request.username}"
