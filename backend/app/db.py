from deta import Deta, _Base

from .settings import SUBABOT_STAGE


def prefix_name(name: str) -> str:
    if SUBABOT_STAGE == "development":
        return f"dev_{name}"

    return name


deta = Deta()  # DETA_PROJECT_KEY
db_feeds = deta.Base(prefix_name("feeds"))
db_keywords = deta.Base(prefix_name("keywords"))
db_events = deta.Base(prefix_name("events"))
db_slack = deta.Base(prefix_name("slack"))


def fetch_all(db: _Base):
    res = db.fetch()
    items = res.items

    # continue fetching until "res.last" is None
    while res.last:
        res = db.fetch(last=res.last)
        items += res.items

    return items
