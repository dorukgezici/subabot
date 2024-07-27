import asyncio
from .subabot.flows import rss_crawler


if __name__ == "__main__":
    asyncio.run(rss_crawler.deploy(
        name="subabot",
        work_pool_name="workers",
        image="dorukgezici/subabot:prefect",
    ))
