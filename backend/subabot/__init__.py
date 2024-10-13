import logging

from fastapi.logger import logger

logger.handlers = logging.getLogger("uvicorn").handlers
# `--log-level` arg of uvicorn controls the `uvicorn.access` logger
logger.setLevel(logging.getLogger("uvicorn.access").level)
