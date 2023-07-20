from datetime import datetime


def now_timestamp() -> int:
    return int(datetime.utcnow().timestamp())
