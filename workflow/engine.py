from datetime import datetime, timezone
from typing import Optional

from workflow.session import SessionState, RequestState

def _now():
    return datetime.now(timezone.utc)

def get_current_request(session: SessionState) -> Optional[RequestState]:
    """
    Returns the RequestState at the current index,
    or None if the session is complete.
    """
    if session.current_index >= len(session.order):
        return None

    username = session.order[session.current_index]
    return session.requests[username]


def mark_opened(session: SessionState) -> None:
    """
    Marks the current request as opened.
    """
    request = get_current_request(session)
    if not request:
        return

    request.last_opened_at = _now()
    session.last_updated_at = _now()

def mark_completed(session: SessionState) -> bool:
    """
    Marks the current request as completed ONLY if it was opened.
    Returns True if successful, False otherwise.
    """
    request = get_current_request(session)
    if not request:
        return False

    if request.last_opened_at is None:
        return False  # invariant violation

    request.status = "completed"
    request.completed_at = _now()

    session.current_index += 1
    session.last_updated_at = _now()
    return True


def mark_skipped(session: SessionState) -> bool:
    """
    Skips the current request ONLY if it was opened.
    """
    request = get_current_request(session)
    if not request:
        return False

    if request.last_opened_at is None:
        return False

    request.status = "skipped"

    session.current_index += 1
    session.last_updated_at = _now()
    return True


def has_more(session: SessionState) -> bool:
    return session.current_index < len(session.order)
