import json
from typing import Annotated, Any, Dict, Literal, Optional, Union

from fastapi import Form


class CommandForm:
    def __init__(
        self,
        token: Annotated[str, Form(...)],
        command: Annotated[str, Form(...)],
        response_url: Annotated[str, Form(...)],
        trigger_id: Annotated[str, Form(...)],
        user_id: Annotated[str, Form(...)],
        user_name: Annotated[str, Form(...)],
        team_id: Annotated[str, Form(...)],
        team_domain: Annotated[str, Form(...)],
        channel_id: Annotated[str, Form(...)],
        channel_name: Annotated[str, Form(...)],
        api_app_id: Annotated[str, Form(...)],
        text: Annotated[str, Form()] = "",
        is_enterprise_install: Annotated[bool, Form()] = False,
        enterprise_id: Annotated[Optional[str], Form()] = None,
        enterprise_name: Annotated[Optional[str], Form()] = None,
    ) -> None:
        self.token = token
        self.command = command
        self.response_url = response_url
        self.trigger_id = trigger_id
        self.user_id = user_id
        self.user_name = user_name
        self.team_id = team_id
        self.team_domain = team_domain
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.api_app_id = api_app_id

        self.text = text
        self.is_enterprise_install = is_enterprise_install
        self.enterprise_id = enterprise_id
        self.enterprise_name = enterprise_name


class PayloadForm:
    response_url: str
    message: Union[Dict[Literal["bot_id", "type", "text", "user", "ts", "app_id", "blocks", "team"], Any], None]
    action: Dict[Literal["type", "block_id", "action_id", "value", "action_ts"], str]
    channel: Dict[Literal["id", "name"], str]
    team: Dict[Literal["id", "domain"], str]

    def __init__(self, payload: Annotated[str, Form(...)]) -> None:
        self.payload = json.loads(payload)

        self.response_url = self.payload["response_url"]
        self.message = self.payload.get("message")
        self.action = self.payload["actions"][0]
        self.channel = self.payload["channel"]
        self.team = self.payload["team"]
