from deta import Deta

from .settings import DETA_PROJECT_KEY
from .utils import DBContext, _prefix

deta = Deta(DETA_PROJECT_KEY)

get_db_feeds = lambda: DBContext(deta, "feeds")
get_db_keywords = lambda: DBContext(deta, "keywords")
get_db_events = lambda: DBContext(deta, "events")
get_db_history = lambda: DBContext(deta, "history")

drive = deta.Drive(_prefix("slack"))
