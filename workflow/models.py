from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Literal


@dataclass(frozen=True)
class PendingRequest:
    """
    Immutable representation of a pending follow request
    derived from Instagram export data.
    """
    username: str
    profile_url: str
    requested_at: datetime


@dataclass
class RequestState:
    """
    Mutable state tracking user progress for a single request.
    """
    username: str
    status: Literal["pending", "completed", "skipped"] = "pending"
    last_opened_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
