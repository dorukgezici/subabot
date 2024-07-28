import os.path
import sys
import asyncio
from prefect import flow

from subabot.rss.crawler import run_crawler as _run_crawler

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


@flow(log_prints=True)
async def rss_crawler():
    return await _run_crawler()


async def deploy():
    flow = await rss_crawler.from_source(
        source="https://github.com/dorukgezici/subabot.git",
        entrypoint="./backend/subabot/flows.py:rss_crawler",
    )
    await flow.deploy(
        name="subabot",
        work_pool_name="workers",
    )

def deploy_sync():
    asyncio.run(deploy())

if __name__ == "__main__":
   deploy_sync()
