from prefect import flow, task

from .rss.crawler import run_crawler as _run_crawler


@flow(log_prints=True)
async def rss_crawler():
    await _run_crawler()
