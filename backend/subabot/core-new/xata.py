from xata.client import XataClient
from .settings import XATA_DATABASE_URL, XATA_BRANCH, XATA_API_KEY

xata = XataClient(
    api_key=XATA_API_KEY,
    db_url=XATA_DATABASE_URL,
    branch_name=XATA_BRANCH,
)
