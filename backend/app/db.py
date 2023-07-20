from deta import Deta

deta = Deta()  # DETA_PROJECT_KEY
db_feeds = deta.Base('feeds')
db_keywords = deta.Base('keywords')
db_events = deta.Base('events')
