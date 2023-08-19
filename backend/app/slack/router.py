import html
from typing import Annotated, Optional

from fastapi import Body, Depends, FastAPI
from fastapi.responses import RedirectResponse
from pydantic import HttpUrl, ValidationError
from slack_sdk.oauth.installation_store import Installation
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.webhook.async_client import AsyncWebhookClient
from slugify import slugify
from starlette.status import HTTP_307_TEMPORARY_REDIRECT

from ..core import db_feeds, db_keywords, fetch_all
from ..core.settings import BACKEND_URL, FRONTEND_URL, SLACK_CLIENT_ID, SLACK_CLIENT_SECRET
from ..rss import Feed, Keyword, crawl_feed
from .blocks import Feedback, generate_configuration_blocks
from .cmd import router as cmd_router
from .dependencies import PayloadForm
from .middlewares import SignatureVerifierMiddleware
from .store import installation_store

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

        return RedirectResponse(FRONTEND_URL, status_code=HTTP_307_TEMPORARY_REDIRECT)

    return f"Something is wrong with the installation (error: {html.escape(str(error or ''))})", 400


@app.post("/events")
def handle_events(body: dict = Body(...)):
    # Slack events URL verification
    if body.get("type") == "url_verification":
        return body


@app.post("/response")
async def handle_response(payload: Annotated[PayloadForm, Depends()]):
    client = AsyncWebhookClient(payload.response_url)

    async with db_feeds as db_f, db_keywords as db_k:
        feeds = [Feed(**feed) for feed in await fetch_all(db_f)]
        keywords = [Keyword(**keyword) for keyword in await fetch_all(db_k)]

        feedback: Feedback = {}
        action_id, channel_id = payload.action.get("action_id"), payload.channel.get("id")

        # Feed management
        if action_id == "add_feed":
            url = payload.action.get("value")

            if not url or len(url) < 11:
                feedback["feed"] = ":warning: Please enter a full URL including `https://`."

            elif url in [f.key.unicode_string() for f in feeds]:
                feedback["feed"] = f":warning: Feed `{url}` is already in the list."

            else:
                try:
                    http_url = HttpUrl(url=url)
                    feed = Feed(key=http_url, title=http_url.unicode_host() or url)
                    await crawl_feed(feed, keywords)
                except (ValidationError, Exception) as e:
                    feedback["feed"] = f":warning: {e}"
                else:
                    new_feed = await db_f.get(url)
                    feeds.append(Feed(**(new_feed or feed.model_dump())))

        elif action_id == "remove_feed":
            url = payload.action.get("value")

            if url and url in [f.key.unicode_string() for f in feeds]:
                await db_f.delete(url)
                feeds = [f for f in feeds if f.key.unicode_string() != url]

        # Keyword management
        elif action_id == "add_keyword":
            value = payload.action.get("value")

            if not value or len(value) < 3:
                feedback["keyword"] = ":warning: Please enter a keyword that is at least 3 characters long."

            elif value in [k.value for k in keywords]:
                feedback["keyword"] = f":warning: Keyword `{value}` is already in the list."

            else:
                new_keyword = Keyword(key=slugify(value), value=value)
                await db_k.put(new_keyword.model_dump())
                keywords.append(new_keyword)

        elif action_id == "remove_keyword":
            key = payload.action.get("value")

            if key and key in [k.key for k in keywords]:
                await db_k.delete(key)
                keywords = [k for k in keywords if k.key != key]

        # Channel management
        elif action_id == "set_channel":
            # TODO: implement
            feedback["channel"] = ":warning: This feature is not implemented yet."

    await client.send(
        blocks=generate_configuration_blocks(
            feeds=feeds,
            keywords=keywords,
            channel=channel_id,
            feedback=feedback,
        ),
    )
