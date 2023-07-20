import logging
from datetime import datetime

from fastapi import FastAPI

from .db import base
from .models import Action

logger = logging.getLogger(__name__)
app = FastAPI(title='Subabot', version='0.1.0')


@app.on_event('startup')
async def on_startup():
    logger.info("Starting up...")


@app.get('/')
async def health():
    return {'status': 'ok'}


# Deta Space Scheduled Actions
@app.post('/__space/v0/actions')
def actions(action: Action) -> None:
    event = action.event.model_dump()
    event['created_at'] = str(datetime.utcnow())
    base.put(event)
