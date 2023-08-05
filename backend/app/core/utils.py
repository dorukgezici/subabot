from calendar import timegm
from datetime import datetime
from typing import Any, Dict, List

from deta import _Base

from .settings import STAGE


def _prefix(name: str) -> str:
    if STAGE == "production":
        return name

    return f"{STAGE[:3]}_{name}"


def now_timestamp() -> int:
    return timegm(datetime.utcnow().timetuple())


def fetch_all(db: _Base) -> List[Dict[str, Any]]:
    res = db.fetch()
    items: List[Dict[str, Any]] = res.items or []

    # continue fetching until "res.last" is None
    while res.last:
        res = db.fetch(last=res.last)
        items += res.items

    return items
