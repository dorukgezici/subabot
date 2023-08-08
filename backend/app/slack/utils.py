from typing import Dict, List, Literal, Optional

from fastapi import HTTPException
from slack_sdk.web.async_client import AsyncWebClient

from ..core.settings import SLACK_CHANNEL_ID, SLACK_TEAM_ID
from ..rss import run_crawler
from .store import installation_store


async def get_client(
    team_id: Optional[str] = SLACK_TEAM_ID,
    enterprise_id: Optional[str] = None,
    is_enterprise_install: Optional[bool] = False,
):
    bot = await installation_store.async_find_bot(
        # The workspace's ID
        team_id=team_id,
        # in the case where this app gets a request from an Enterprise Grid workspace
        enterprise_id=enterprise_id,
        is_enterprise_install=is_enterprise_install,
    )

    if not (bot_token := bot.bot_token if bot else None):
        # The app may be uninstalled or be used in a shared channel
        raise HTTPException(status_code=403, detail=f"not authorized for team {team_id}")

    return AsyncWebClient(token=bot_token)


async def crawl_and_alert():
    # Slack client
    client = await get_client()

    async for entries in run_crawler():
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Found <{entry['link']}|{entry['title']}>.",
                },
            }
            for entry in entries
        ]

        if len(blocks) > 0:
            await client.chat_postMessage(
                channel=SLACK_CHANNEL_ID,
                text="New entries found!",
                blocks=blocks,
            )


def configure_blocks(
    keywords: List[str],
    channel: str,
    unfurls: int,
    notifications: int,
    feedback: Optional[Dict[Literal["keyword", "channel"], str]] = None,
):
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":hammer_and_wrench:  Bot Configuration  :hammer_and_wrench:",
            },
        },
        {
            "type": "context",
            "block_id": "stats",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Current Usage: {unfurls} link previews shown, {notifications} notifications sent |  <https://slack.com/apps/A03QV0U65HN|More Configuration Settings>",
                },
            ],
        },
        {
            "type": "divider",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":bulb: KEYWORDS :bulb:",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Here's the list of keywords that you're currently tracking:"
                if len(keywords) > 0
                else "_No keywords configured yet._",
            },
        },
        *[
            {
                "type": "section",
                "block_id": f"keyword_{keyword}",
                "text": {
                    "type": "mrkdwn",
                    "text": f"`{keyword}`",
                },
                "accessory": {
                    "action_id": "remove_keyword",
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Remove",
                    },
                    "value": keyword,
                },
            }
            for keyword in keywords
        ],
        {
            "type": "input",
            "dispatch_action": True,
            "element": {
                "type": "plain_text_input",
                "action_id": "add_keyword",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Add a keyword (must be between 3 and 30 characters)",
                },
                "dispatch_action_config": {
                    "trigger_actions_on": ["on_enter_pressed"],
                },
                "min_length": 3,
                "max_length": 30,
                "focus_on_load": True,
            },
            "label": {
                "type": "plain_text",
                "text": " ",
            },
        },
        *(
            [
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": feedback["keyword"],
                        },
                    ],
                },
            ]
            if feedback
            else []
        ),
        # {
        #     "type": "divider",
        # },
        # {
        #     "type": "section",
        #     "text": {
        #         "type": "mrkdwn",
        #         "text": ":hash: CHANNEL :hash:",
        #     },
        # },
        # {
        #     "type": "section",
        #     "text": {
        #         "type": "mrkdwn",
        #         "text": "Select a public channel to receive notifications in:",
        #     },
        #     "accessory": {
        #         "action_id": "set_channel",
        #         "type": "conversations_select",
        #         "placeholder": {
        #             "type": "plain_text",
        #             "text": "Select a channel...",
        #             "emoji": True,
        #         },
        #         **({"initial_conversation": channel} if channel else {}),
        #     },
        # },
        # *(
        #     [
        #         {
        #             "type": "context",
        #             "elements": [
        #                 {
        #                     "type": "mrkdwn",
        #                     "text": feedback["channel"],
        #                 },
        #             ],
        #         },
        #     ]
        #     if feedback
        #     else []
        # ),
    ]
