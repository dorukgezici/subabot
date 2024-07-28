import logging

from fastapi.logger import logger
from subabot.rss.crawler import run_crawler

logger.handlers = logging.getLogger("uvicorn").handlers
# `--log-level` arg of uvicorn controls the `uvicorn.access` logger
logger.setLevel(logging.getLogger("uvicorn.access").level)
