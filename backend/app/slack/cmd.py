from asyncer import asyncify

from ..db import db_keywords, fetch_all


async def configure():
    pass


async def keywords():
    return await asyncify(fetch_all)(db=db_keywords)
