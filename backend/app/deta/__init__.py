from deta.base import _Base

from .models import Action, Event
from .router import router


def fetch_all(db: _Base):
    res = db.fetch()
    items = res.items

    # Continue fetching until "res.last" is None.
    while res.last:
        res = db.fetch(last=res.last)
        items += res.items

    return items
