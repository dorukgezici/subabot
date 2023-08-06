import os

STAGE = os.environ.get("SUBABOT_STAGE", "development")
BACKEND_URL = os.environ.get("SUBABOT_BACKEND_URL", "http://localhost:8000")

DETA_PROJECT_KEY = os.environ.get("DETA_PROJECT_KEY", "")

SLACK_CLIENT_ID = os.environ.get("SLACK_CLIENT_ID", "")
SLACK_CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET", "")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")

SLACK_TEAM_ID = os.environ.get("SLACK_TEAM_ID", "T05H4RS4UG5")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID", "C05HA7AU7EG")
