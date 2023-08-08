from .crawler import run_crawler
from .models import Feed, History, Keyword

FEEDS: list[Feed] = [
    Feed(key="hackernews", title="Hacker News", url="https://hnrss.org/newest"),
    Feed(key="cointelegraph", title="Cointelegraph", url="https://cointelegraph.com/rss"),
]

KEYWORDS: list[Keyword] = [
    Keyword(key="bitcoin", value="Bitcoin"),
    Keyword(key="ethereum", value="Ethereum"),
    Keyword(key="dogecoin", value="Dogecoin"),
]

__all__ = ["run_crawler", "Feed", "History", "Keyword", "FEEDS", "KEYWORDS"]
