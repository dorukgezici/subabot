from typing import Dict, List, Literal, Optional

from subabot.config import SLACK_APP_ID
from subabot.rss.models import Feed, Keyword

Feedback = Dict[Literal["feed", "keyword", "channel"], str]


def generate_configuration_blocks(
    feeds: List[Feed],
    keywords: List[Keyword],
    channel: Optional[str],
    feedback: Optional[Feedback] = None,
):
    return [
        ####################
        # header
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
                    "text": f"Current Usage: {len(feeds)} feeds, {len(keywords)} keywords"
                    f" | <https://slack.com/apps/{SLACK_APP_ID}|More Configuration Settings>",
                },
            ],
        },
        {"type": "divider"},
        ####################
        # feeds
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": ":newspaper:  RSS FEEDS  :newspaper:"},
        },
        *(
            [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "_No feeds configured yet._",
                    },
                }
            ]
            if len(feeds) == 0
            else []
        ),
        *[
            {
                "type": "section",
                "block_id": f"feed_{feed.key}",
                "text": {"type": "mrkdwn", "text": f"{feed.title}: `{feed.key}`"},
                "accessory": {
                    "action_id": "remove_feed",
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Remove"},
                    "value": str(feed.key),
                },
            }
            for feed in feeds
        ],
        {
            "type": "input",
            "dispatch_action": True,
            "element": {
                "type": "url_text_input",
                "action_id": "add_feed",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Add a feed (must be a full RSS URL)",
                },
                "dispatch_action_config": {
                    "trigger_actions_on": ["on_enter_pressed"],
                },
            },
            "label": {"type": "plain_text", "text": " "},
        },
        *(
            [
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": feedback["feed"],
                        },
                    ],
                },
            ]
            if feedback and "feed" in feedback
            else []
        ),
        {"type": "divider"},
        ####################
        # keywords
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":bulb:  KEYWORDS  :bulb:",
            },
        },
        *(
            [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "_No keywords configured yet._",
                    },
                }
            ]
            if len(keywords) == 0
            else []
        ),
        *[
            {
                "type": "section",
                "block_id": f"keyword_{keyword.key}",
                "text": {
                    "type": "mrkdwn",
                    "text": f"`{keyword.value}`",
                },
                "accessory": {
                    "action_id": "remove_keyword",
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Remove",
                    },
                    "value": keyword.key,
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
            "label": {"type": "plain_text", "text": " "},
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
            if feedback and "keyword" in feedback
            else []
        ),
        {"type": "divider"},
        ####################
        # channel
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":hash:  CHANNEL  :hash:",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Select a public channel to receive notifications in:",
            },
            "accessory": {
                "action_id": "set_channel",
                "type": "conversations_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select a channel...",
                    "emoji": True,
                },
                **({"initial_conversation": channel} if channel else {}),
            },
        },
        *(
            [
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": feedback["channel"],
                        },
                    ],
                },
            ]
            if feedback and "channel" in feedback
            else []
        ),
    ]
