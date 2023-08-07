import html
import json
from typing import Annotated, Optional

from fastapi import Body, Depends, FastAPI, Form
from slack_sdk.oauth.installation_store import Installation
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.webhook.async_client import AsyncWebhookClient
from slugify import slugify

from ..core import db_keywords, fetch_all
from ..core.settings import BACKEND_URL, SLACK_CLIENT_ID, SLACK_CLIENT_SECRET
from ..rss import Keyword
from .cmd import router as cmd_router
from .dependencies import PayloadForm
from .middlewares import SignatureVerifierMiddleware
from .store import installation_store
from .utils import configure_blocks

app = FastAPI(title="Subabot Slack App", version="0.1.0")
app.add_middleware(SignatureVerifierMiddleware)
app.include_router(cmd_router, prefix="/cmd")


@app.get("/oauth")
async def handle_oauth(code: str, error: Optional[str] = None):
    # Retrieve the auth code and state from the request params
    if code:
        client = AsyncWebClient()  # no prepared token needed for this
        # Complete the installation by calling oauth.v2.access API method
        oauth_response = await client.oauth_v2_access(
            client_id=SLACK_CLIENT_ID,
            client_secret=SLACK_CLIENT_SECRET,
            redirect_uri=f"{BACKEND_URL}/slack/oauth",
            code=code,
        )

        installed_enterprise = oauth_response.get("enterprise", {})
        is_enterprise_install = oauth_response.get("is_enterprise_install", False)
        installed_team = oauth_response.get("team", {})
        installer = oauth_response.get("authed_user", {})
        incoming_webhook = oauth_response.get("incoming_webhook", {})
        bot_token = oauth_response.get("access_token")

        # NOTE: oauth.v2.access doesn't include bot_id in response
        bot_id = None
        enterprise_url = None
        if bot_token is not None:
            auth_test = await client.auth_test(token=bot_token)
            bot_id = auth_test["bot_id"]
            if is_enterprise_install is True:
                enterprise_url = auth_test.get("url")

        installation = Installation(
            app_id=oauth_response.get("app_id"),
            enterprise_id=installed_enterprise.get("id") if installed_enterprise else None,
            enterprise_name=installed_enterprise.get("name") if installed_enterprise else None,
            enterprise_url=enterprise_url,
            team_id=installed_team.get("id"),
            team_name=installed_team.get("name"),
            bot_token=bot_token,
            bot_id=bot_id,
            bot_user_id=oauth_response.get("bot_user_id"),
            bot_scopes=oauth_response.get("scope", ""),  # comma-separated string
            user_id=installer.get("id", ""),
            user_token=installer.get("access_token", ""),
            user_scopes=installer.get("scope", ""),  # comma-separated string
            incoming_webhook_url=incoming_webhook.get("url"),
            incoming_webhook_channel=incoming_webhook.get("channel"),
            incoming_webhook_channel_id=incoming_webhook.get("channel_id"),
            incoming_webhook_configuration_url=incoming_webhook.get("configuration_url"),
            is_enterprise_install=is_enterprise_install,
            token_type=oauth_response.get("token_type"),
        )

        # Store the installation
        installation_store.save(installation)

        return "Thanks for installing this app!"

    return f"Something is wrong with the installation (error: {html.escape(str(error or ''))})", 400


@app.post("/events")
def handle_events(
    body: dict = Body(...),
    command: str = Form(),
    # enterprise_id: str = Form(...),
    # team_id: str = Form(...),
    # trigger_id: str = Form(...),
    payload: str = Form(),
):
    # Slack events URL verification
    if body.get("type") == "url_verification":
        return body

    # Handle a slash command invocation
    # if command == "/open-modal":
    #     try:
    #         # Lookup the stored bot token for this workspace
    #         bot = installation_store.find_bot(
    #             # in the case where this app gets a request from an Enterprise Grid workspace
    #             enterprise_id=enterprise_id,
    #             # The workspace's ID
    #             team_id=team_id,
    #         )
    #         bot_token = bot.bot_token if bot else None
    #         if not bot_token:
    #             # The app may be uninstalled or be used in a shared channel
    #             return "Please install this app first!", 200

    #         # Open a modal using the valid bot token
    #         client = WebClient(token=bot_token)
    #         response = client.views_open(
    #             trigger_id=trigger_id,
    #             view={
    #                 "type": "modal",
    #                 "callback_id": "modal-id",
    #                 "title": {"type": "plain_text", "text": "Awesome Modal"},
    #                 "submit": {"type": "plain_text", "text": "Submit"},
    #                 "blocks": [
    #                     {
    #                         "type": "input",
    #                         "block_id": "b-id",
    #                         "label": {
    #                             "type": "plain_text",
    #                             "text": "Input label",
    #                         },
    #                         "element": {
    #                             "action_id": "a-id",
    #                             "type": "plain_text_input",
    #                         },
    #                     }
    #                 ],
    #             },
    #         )
    #         return "", 200
    #     except SlackApiError as e:
    #         code = e.response["error"]
    #         return f"Failed to open a modal due to {code}", 200

    if payload:
        # Data submission from the modal
        payload_dict: dict = json.loads(payload)
        if payload_dict["type"] == "view_submission" and payload_dict["view"]["callback_id"] == "modal-id":
            submitted_data = payload_dict["view"]["state"]["values"]
            print(submitted_data)  # {'b-id': {'a-id': {'type': 'plain_text_input', 'value': 'your input'}}}
            # You can use WebClient with a valid token here too
            return "", 200

    # Indicate unsupported request patterns
    return "", 404


@app.post("/response")
async def handle_response(payload: Annotated[PayloadForm, Depends()]):
    client = AsyncWebhookClient(payload.response_url)

    async with db_keywords as db:
        keywords = [keyword["value"] for keyword in await fetch_all(db)]

        if payload.action["action_id"] == "add_keyword":
            keyword, feedback = payload.action.get("value"), None

            if not keyword or len(keyword) < 3:
                feedback = ":warning: Please enter a keyword that is at least 3 characters long."

            elif keyword in keywords:
                feedback = f":warning: Keyword `{keyword}` is already in the list."

            else:
                await db.put(Keyword(key=slugify(keyword), value=keyword).model_dump())
                keywords.append(keyword)

            await client.send(
                blocks=configure_blocks(
                    keywords=keywords,
                    channel=payload.channel["id"],
                    unfurls=0,
                    notifications=0,
                    feedback={"keyword": feedback} if feedback else None,
                ),
            )
