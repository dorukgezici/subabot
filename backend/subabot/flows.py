import asyncio
from prefect import flow, task

from subabot.rss.crawler import run_crawler


async def deploy():
    flow = await run_crawler.from_source(
        source="https://github.com/dorukgezici/subabot.git",
        entrypoint="./backend/subabot/flows.py:run_crawler",
    )
    await flow.deploy(
        name="subabot",
        work_pool_name="workers",
    )

def deploy_sync():
    asyncio.run(deploy())

if __name__ == "__main__":
   deploy_sync()
