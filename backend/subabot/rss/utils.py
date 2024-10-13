from calendar import timegm
from datetime import datetime


def now_timestamp() -> int:
    return timegm(datetime.utcnow().timetuple())
