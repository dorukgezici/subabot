from .models import Feed, Keyword
from .utils import run_crawler

feeds: list[Feed] = [
    Feed(key='hackernews', title='Hacker News', url='https://hnrss.org/newest'),
    Feed(key='cointelegraph', title='Cointelegraph', url='https://cointelegraph.com/rss'),
]

keywords: list[Keyword] = [
    Keyword(key='bitcoin', value='Bitcoin'),
    Keyword(key='ethereum', value='Ethereum'),
    Keyword(key='dogecoin', value='Dogecoin'),
]
