import ipaddress
import re
import socket
from urllib.parse import urlsplit, urlunsplit

from aiohttp.abc import AbstractResolver
from aiohttp.resolver import ThreadedResolver


def public_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        return address.is_global and not address.is_multicast
    except ValueError:
        return False


def safe_url(value: str) -> str:
    """Syntactic check. DNS is checked on the actual connection, never ahead of it."""
    if not isinstance(value, str) or len(value) > 2048 or re.search(r"[\x00-\x20\x7f\\]", value):
        raise ValueError("Use a valid public HTTP or HTTPS URL.")
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Use a valid public HTTP or HTTPS URL.") from exc
    if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
        raise ValueError("Use a public HTTP or HTTPS URL without a username or password.")
    if port not in {None, 80, 443} or host.lower().rstrip(".") == "localhost":
        raise ValueError("Local addresses and nonstandard ports are not allowed.")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if "." not in host or host.lower().endswith((".local", ".localhost", ".internal", ".test")):
            raise ValueError("Use a public internet hostname.") from None
    else:
        if not public_ip(host):
            raise ValueError("Private or reserved network addresses are not allowed.")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))


def safe_webhook(value: str) -> str:
    value = safe_url(value.strip())
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"hooks.slack.com", "hooks.slack-gov.com"}
        or parsed.port is not None
        or parsed.query
        or not re.fullmatch(r"/services/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+", parsed.path)
    ):
        raise ValueError("Paste a Slack incoming webhook URL beginning with https://hooks.slack.com/services/.")
    return value


class PublicResolver(AbstractResolver):
    """The connector uses these exact checked addresses, preventing DNS rebinding."""

    def __init__(self):
        self.resolver = ThreadedResolver()

    async def resolve(self, host, port=0, family=socket.AF_INET):
        results = await self.resolver.resolve(host, port, family)
        if not results or any(not public_ip(result["host"]) for result in results):
            raise OSError("Feed host resolves to a private or reserved network address.")
        return results

    async def close(self):
        await self.resolver.close()
