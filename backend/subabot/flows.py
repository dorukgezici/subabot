import asyncio
from prefect import flow, task

from .rss.crawler import run_crawler as _run_crawler


@flow(log_prints=True)
async def rss_crawler():
    await _run_crawler()


if __name__ == "__main__":
    asyncio.run(rss_crawler.deploy(
        name="subabot",
        work_pool_name="workers",
        image="dorukgezici/subabot:prefect",
    ))
