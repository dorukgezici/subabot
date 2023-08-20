from deta import Deta

from .settings import DETA_PROJECT_KEY
from .utils import DBContext, _prefix

deta = Deta(DETA_PROJECT_KEY)

get_db_keywords = lambda: DBContext(deta, "keywords")
get_db_feeds = lambda: DBContext(deta, "feeds")
get_db_crawls = lambda: DBContext(deta, "crawls")
get_db_searches = lambda: DBContext(deta, "searches")
get_db_history = lambda: DBContext(deta, "history")
get_db_events = lambda: DBContext(deta, "events")

drive = deta.Drive(_prefix("slack"))
