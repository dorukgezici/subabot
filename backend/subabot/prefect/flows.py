import asyncio
from prefect import flow, task

from subabot.rss.crawler import run_crawler as _run_crawler


@flow(log_prints=True)
async def rss_crawler():
    await _run_crawler()


if __name__ == "__main__":
    async def main():
        flow = await rss_crawler.from_source(
            source="https://github.com/dorukgezici/subabot.git",
            entrypoint="./backend/subabot/prefect/flows.py:rss_crawler",
        )
        await flow.deploy(
            name="subabot",
            work_pool_name="workers",
        )

    asyncio.run(main())
