from asyncer import asyncify
from fastapi import HTTPException, Request
from slack_sdk.signature import SignatureVerifier
from starlette.status import HTTP_403_FORBIDDEN
from starlette.types import ASGIApp, Receive, Scope, Send

from subabot.config import settings

signature_verifier = SignatureVerifier(signing_secret=settings.slack_signing_secret)


class SignatureVerifierMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def verify_signature():
            message = await receive()
            assert message["type"] == "http.request"
            request = Request(scope)

            # Slack signature verification
            if not await asyncify(signature_verifier.is_valid)(
                body=message.get("body", b""),
                timestamp=request.headers.get("X-Slack-Request-Timestamp", ""),
                signature=request.headers.get("X-Slack-Signature", ""),
            ):  # type: ignore
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid signature")

            return message

        await self.app(scope, verify_signature, send)
