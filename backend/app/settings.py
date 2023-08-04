import os

SUBABOT_STAGE = os.environ.get("SUBABOT_STAGE", "development")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
SLACK_CLIENT_ID = os.environ.get("SLACK_CLIENT_ID", "")
SLACK_CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET", "")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")
