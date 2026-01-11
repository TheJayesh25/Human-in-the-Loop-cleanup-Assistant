import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from workflow.models import PendingRequest


def parse_pending_follow_requests(
    json_path: str | Path,
) -> List[PendingRequest]:
    """
    Parse Instagram's pending_follow_requests.json file into
    a list of PendingRequest objects.
    """
    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    try:
        entries = raw_data["relationships_follow_requests_sent"]
    except KeyError:
        raise ValueError(
            "Invalid Instagram export: "
            "missing 'relationships_follow_requests_sent'"
        )

    pending_requests: List[PendingRequest] = []

    for entry in entries:
        string_data = entry.get("string_list_data", [])

        for item in string_data:
            username = item.get("value")
            profile_url = item.get("href")
            timestamp = item.get("timestamp")

            if not (username and profile_url and timestamp):
                # Skip malformed records safely
                continue

            requested_at = datetime.fromtimestamp(
                timestamp, tz=timezone.utc
            )

            pending_requests.append(
                PendingRequest(
                    username=username,
                    profile_url=profile_url,
                    requested_at=requested_at,
                )
            )

    return pending_requests
