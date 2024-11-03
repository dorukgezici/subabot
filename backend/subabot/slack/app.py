import html
from typing import Annotated, Optional

from fastapi import BackgroundTasks, Body, Depends, FastAPI
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from slack_sdk.oauth.installation_store import Installation
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.webhook.async_client import AsyncWebhookClient
from starlette.status import HTTP_307_TEMPORARY_REDIRECT

from subabot.config import settings
from subabot.db import SessionDep
from subabot.rss.crawler import crawl_feed
from subabot.rss.models import Feed, Keyword
from subabot.slack.blocks import Feedback, generate_configuration_blocks
from subabot.slack.cmd import router as cmd_router
from subabot.slack.dependencies import PayloadForm
from subabot.slack.middlewares import SignatureVerifierMiddleware
from subabot.slack.store import installation_store

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
            client_id=settings.slack_client_id,
            client_secret=settings.slack_client_secret,
            redirect_uri=f"{settings.subabot_backend_url}/slack/oauth",
            code=code,
        )  # type: ignore

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
            auth_test = await client.auth_test(token=bot_token)  # type: ignore
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

        return RedirectResponse(settings.subabot_frontend_url, status_code=HTTP_307_TEMPORARY_REDIRECT)

    return f"Something is wrong with the installation (error: {html.escape(str(error or ''))})", 400


@app.post("/events")
def handle_events(body: dict = Body(...)):
    # Slack events URL verification
    if body.get("type") == "url_verification":
        return body


@app.post("/response")
async def handle_response(
    payload: Annotated[PayloadForm, Depends()],
    session: SessionDep,
    background_tasks: BackgroundTasks,
):
    client = AsyncWebhookClient(payload.response_url)

    feeds = list(Feed.list(session))
    keywords = list(Keyword.list(session))

    feedback: Feedback = {}
    action_id, channel_id = payload.action.get("action_id"), payload.channel.get("id")

    # Feed management
    if action_id == "add_feed":
        url = payload.action.get("value")

        if not url or len(url) < 11:
            feedback["feed"] = ":warning: Please enter a full URL including `https://`."
        elif url in [f.key for f in feeds]:
            feedback["feed"] = f":warning: Feed `{url}` is already in the list."
        else:
            try:
                feed = Feed.upsert(session, key=url)
            except (ValidationError, Exception) as e:
                feedback["feed"] = f":warning: {e}"
            else:
                feeds.append(feed)
                background_tasks.add_task(crawl_feed, feed, keywords)

    elif action_id == "remove_feed":
        try:
            url = payload.action["value"]
            Feed.delete(url, session)
        except (ValidationError, Exception) as e:
            feedback["feed"] = f":warning: {e}"
        else:
            feeds = [f for f in feeds if f.key != url]

    # Keyword management
    elif action_id == "add_keyword":
        value = payload.action.get("value")

        if not value or len(value) < 3:
            feedback["keyword"] = ":warning: Please enter a keyword that is at least 3 characters long."
        elif value in [k.value for k in keywords]:
            feedback["keyword"] = f":warning: Keyword `{value}` is already in the list."
        else:
            new_keyword = Keyword.upsert(session, value=value)
            keywords.append(new_keyword)

    elif action_id == "remove_keyword":
        key = payload.action.get("value")

        if key and key in [k.key for k in keywords]:
            Keyword.delete(key, session)
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
        )  # type: ignore
    )
