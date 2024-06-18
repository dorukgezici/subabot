from calendar import timegm
from datetime import datetime
from typing import Any, Dict, List

from deta import Deta
from deta._async.client import _AsyncBase

from .settings import STAGE


def _prefix(name: str) -> str:
    if STAGE == "production":
        return name

    return f"{STAGE[:3]}_{name}"


def now_timestamp() -> int:
    return timegm(datetime.utcnow().timetuple())


class DBContext:
    def __init__(self, deta: Deta, name: str) -> None:
        self.deta = deta
        self.name = _prefix(name)

    async def __aenter__(self) -> _AsyncBase:
        self.db = self.deta.AsyncBase(self.name)
        return self.db

    async def __aexit__(self, *args):
        await self.db.close()


async def fetch_all(db: _AsyncBase) -> List[Dict[str, Any]]:
    res = await db.fetch()
    items: List[Dict[str, Any]] = res.items or []

    # continue fetching until "res.last" is None
    while res.last:
        res = await db.fetch(last=res.last)
        items += res.items

    return items
