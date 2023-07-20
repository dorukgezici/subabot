from fastapi import FastAPI

from .models import Action

app = FastAPI(title="Subabot", version="0.1.0")


@app.on_event("startup")
async def on_startup():
    print("Starting up...")


@app.get("/")
async def read_root():
    return {"status": "up"}


# Deta Space Scheduled Actions
@app.post('/__space/v0/actions')
def actions(action: Action):
    data = action.dict()
    event = data['event']
    print(f"Received event: {event['id']}")

    if event['id'] == 'cleanup':
        # cleanup()
        pass
