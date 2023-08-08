from deta import Deta

from .settings import DETA_PROJECT_KEY
from .utils import DBContext, _prefix

deta = Deta(DETA_PROJECT_KEY)

db_feeds = DBContext(deta, "feeds")
db_keywords = DBContext(deta, "keywords")
db_events = DBContext(deta, "events")
db_history = DBContext(deta, "history")

drive = deta.Drive(_prefix("slack"))
