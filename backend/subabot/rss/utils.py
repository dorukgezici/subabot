from typing import Any, Generator, Sequence, Union

from feedparser import FeedParserDict
from sqlmodel import select

from subabot.db import Session, engine
from subabot.rss.models import History


def find_matches(
    data: Union[list[FeedParserDict], dict, str],
    keyword: str,
    pre_path: tuple = (),
) -> Generator[tuple, Any, Any]:
    """Generates tuples of paths to the keyword found in the data."""
    if isinstance(data, list):
        for index, item in enumerate(data):
            path = pre_path + (str(index),)
            yield from find_matches(item, keyword, path)

    elif isinstance(data, dict):
        for key, value in data.items():
            path = pre_path + (key,)
            yield from find_matches(value, keyword, path)

    elif isinstance(data, str) and keyword.casefold() in data.casefold():
        yield pre_path


def get_matching_entries(entries: Sequence[dict], matches: list[tuple]) -> Sequence[dict]:
    """Returns a list of unique entries from the matches that are NOT in history."""

    with Session(engine) as session:
        links = [history.key for history in session.exec(select(History)).all()]

    indexes = set(int(match[0]) for match in matches)
    return [entries[i] for i in indexes if entries[i].get("link") not in links]
