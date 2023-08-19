import os
from pathlib import Path

# Build paths inside the project like this: APP_DIR / 'subdir'.
APP_DIR = Path(__file__).resolve().parent.parent

STAGE = os.environ.get("SUBABOT_STAGE", "development")
BACKEND_URL = os.environ.get("SUBABOT_BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.environ.get("SUBABOT_FRONTEND_URL", "http://localhost:5173")

DETA_PROJECT_KEY = os.environ["DETA_PROJECT_KEY"]

SLACK_CLIENT_ID = os.environ["SLACK_CLIENT_ID"]
SLACK_CLIENT_SECRET = os.environ["SLACK_CLIENT_SECRET"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

SLACK_APP_ID = os.environ["SLACK_APP_ID"]
SLACK_TEAM_ID = os.environ["SLACK_TEAM_ID"]
SLACK_CHANNEL_ID = os.environ["SLACK_CHANNEL_ID"]
