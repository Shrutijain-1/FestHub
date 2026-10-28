"""Small display helpers."""
from datetime import datetime, timezone


def local_datetime_text(value: str) -> str:
    """The server stores UTC; show it in this computer's local time."""
    utc_value = datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    return utc_value.astimezone().strftime("%d %b %Y, %I:%M %p")