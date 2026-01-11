from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
import json
from pathlib import Path

@dataclass
class RequestState:
    username: str
    status: Literal["pending", "completed", "skipped"] = "pending"
    last_opened_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class SessionState:
    session_id: str
    created_at: datetime
    last_updated_at: datetime

    order: List[str]                     # ordered usernames
    current_index: int = 0

    requests: Dict[str, RequestState] = field(default_factory=dict)

from workflow.models import PendingRequest


def initialize_session(
    pending_requests: List[PendingRequest],
    session_id: str,
) -> SessionState:
    now = datetime.now(timezone.utc)

    # Order usernames by requested_at (oldest first)
    ordered = sorted(
        pending_requests,
        key=lambda r: r.requested_at
    )

    order = [r.username for r in ordered]

    request_states = {
        username: RequestState(username=username)
        for username in order
    }

    return SessionState(
        session_id=session_id,
        created_at=now,
        last_updated_at=now,
        order=order,
        current_index=0,
        requests=request_states,
    )

def _dt_to_str(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _str_to_dt(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None

def save_session(session: SessionState, path: str | Path) -> None:
    path = Path(path)

    data = {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "last_updated_at": session.last_updated_at.isoformat(),
        "order": session.order,
        "current_index": session.current_index,
        "requests": {
            username: {
                "status": state.status,
                "last_opened_at": _dt_to_str(state.last_opened_at),
                "completed_at": _dt_to_str(state.completed_at),
            }
            for username, state in session.requests.items()
        },
    }

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_session(path: str | Path) -> SessionState:
    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    session = SessionState(
        session_id=data["session_id"],
        created_at=datetime.fromisoformat(data["created_at"]),
        last_updated_at=datetime.fromisoformat(data["last_updated_at"]),
        order=data["order"],
        current_index=data["current_index"],
        requests={},
    )

    for username, raw in data["requests"].items():
        session.requests[username] = RequestState(
            username=username,
            status=raw["status"],
            last_opened_at=_str_to_dt(raw["last_opened_at"]),
            completed_at=_str_to_dt(raw["completed_at"]),
        )

    return session
