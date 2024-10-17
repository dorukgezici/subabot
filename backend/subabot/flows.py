from prefect import flow

from subabot.rss.crawler import run_crawler as _run_crawler


@flow(log_prints=True)
async def rss_crawler():
    return await _run_crawler()  # type: ignore
