from pydantic import HttpUrl

from .crawler import crawl_feed, run_crawler
from .models import Feed, History, Keyword

FEEDS: list[Feed] = [
    Feed(key=HttpUrl("https://hnrss.org/newest"), title="Hacker News"),
    Feed(key=HttpUrl("https://cointelegraph.com/rss"), title="Cointelegraph"),
]

KEYWORDS: list[Keyword] = [
    Keyword(key="bitcoin", value="Bitcoin"),
    Keyword(key="ethereum", value="Ethereum"),
    Keyword(key="dogecoin", value="Dogecoin"),
]

__all__ = ["crawl_feed", "run_crawler", "Feed", "History", "Keyword", "FEEDS", "KEYWORDS"]
