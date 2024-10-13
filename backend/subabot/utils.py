from calendar import timegm
from datetime import datetime, UTC


def now() -> datetime:
    return datetime.now(UTC)


def now_timestamp() -> int:
    return timegm(now().timetuple())
