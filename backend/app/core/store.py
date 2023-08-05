from deta import Deta

from .settings import DETA_PROJECT_KEY
from .utils import _prefix

deta = Deta(DETA_PROJECT_KEY)

db_feeds = deta.Base(_prefix("feeds"))
db_keywords = deta.Base(_prefix("keywords"))
db_events = deta.Base(_prefix("events"))
db_slack = deta.Base(_prefix("slack"))

drive = deta.Drive(_prefix("slack"))
