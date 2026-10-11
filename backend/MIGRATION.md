# Backend modernization, 11 October 2026

The old service exposed global feed/keyword tables, required Slack OAuth secrets merely to import the app, used Prefect for a small polling loop and had tests that touched the real network and application database. The rebuilt service isolates capability-based workspaces, persists signals and delivery state, has an explicit publishing boundary, and starts without any integration credentials.

## Resolved versions

These are the versions actually resolved and installed from `uv.lock`, after upgrading transitive dependencies as well as direct dependencies. Python is constrained to the 3.14 series and the Docker build uses the same series. `uv sync --frozen` reproduces the dependency set.

| Package | Old requirement | Resolved version |
| --- | --- | --- |
| FastAPI | 0.115.2+ | 0.143.0 |
| Starlette | indirect | 1.7.0 |
| Pydantic | indirect | 2.14.0 |
| pydantic-settings | 2.5.2+ | 2.15.0 |
| SQLModel | 0.0.22+ | 0.0.48 |
| SQLAlchemy | indirect | 2.1.4 |
| aiohttp | 3.10.10+ | 3.14.4 |
| feedparser | 6.0.11+ | 6.0.14 |
| Uvicorn | 0.31.1+ | 0.54.0 |
| pytest | 8.3.3+ | 9.1.1 |
| pytest-asyncio | 0.24.0+ | 1.4.0 |
| Ruff | 0.6.9+ | 0.17.0 |
| HTTPX2 | absent | 2.13.1 |

## Changelog review and changes applied

- [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/): 0.128 removed Pydantic v1 compatibility. Models and validators now use only Pydantic v2. Application startup and teardown use a lifespan context manager. The 0.143 OpenTelemetry change makes exporter auto-configuration opt-in; this application does not depend on automatic exporters.
- [Pydantic changelog](https://pydantic.dev/docs/validation/latest/get-started/changelog/): 2.14 drops Python 3.9 and adds 3.15 support. The project uses stable Python 3.14, explicit input schemas, `model_validate` and `model_dump`. Separate response schemas prevent database fields and secrets from becoming API output. Settings are namespaced and no longer import old secrets implicitly.
- [SQLModel release notes](https://sqlmodel.tiangolo.com/release-notes/): 0.0.45 changed datetime database handling to aware UTC values. Every timestamp producer uses `datetime.now(UTC)` and feed timestamps are converted to UTC. 0.0.48 adds SQLAlchemy 2.1 support. Queries use SQLModel sessions and database uniqueness enforces durable article deduplication.
- [Starlette release notes](https://starlette.dev/release-notes/): 1.7 requires AnyIO 4; the lock resolves a compatible current version. The tests use HTTPX2, following the new TestClient support. The built-in request body limit middleware covers both declared and streamed request sizes, introduced in 1.6.
- [aiohttp changelog](https://docs.aiohttp.org/en/stable/changes.html): updated to 3.14.4. Feed fetching now uses an explicit timeout, checked DNS resolver, controlled redirects and bounded response streaming. Unsolicited compressed content is rejected, rather than allowing decompression to evade the body cap. Proxy environment variables are ignored for outbound requests.
- [Slack Python SDK changelog](https://docs.slack.dev/changelog/): reviewed the current Python SDK release stream, including 3.43.0. The rebuilt MVP uses the documented [incoming webhook API](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/) directly, so the old Slack SDK dependency, OAuth endpoints, installation store and mandatory app secrets were removed. Payloads are Block Kit messages with plain text and an article button. [Slack rate limits](https://docs.slack.dev/apis/web-api/rate-limits/) prescribe roughly one incoming webhook message per second; delivery is paced and failed items remain pending. This is a webhook connection flow, not Marketplace OAuth installation.

## Removed infrastructure

Prefect 3.0.9, Prefect deployment definitions, the old Kubernetes chart, Supabase, asyncer, python-multipart and slugify are removed. None are needed to implement feed polling, persistence, workspace ownership or Slack webhooks. An application lifespan scheduler replaces the Prefect server and worker; the API has one documented worker/replica. The obsolete chart's horizontal scaling was incompatible with process-local coordination and SQLite. A regular Python container replaces the Prefect Kubernetes base image.

## Existing data and credentials

The new database defaults to `subabot.db`; the old application used `database.db`. No existing database or `.env` is overwritten or imported. The data models changed substantially and the old records do not have workspace ownership. Do not point the new service at the old file expecting a migration. If old data matters, preserve a backup and write a one-time, reviewed mapping into a chosen new workspace. This rewrite does not automatically claim or publish anyone's legacy records.

Existing Slack OAuth secrets remain unused. Create an incoming webhook for the intended channel when ready and add it through Settings. The validation suite does not send any actual Slack messages.

## Verification

The test suite covers tenant isolation, capability hashing, input validation, monitor and signal operations, persistence through application restarts, public publication/revocation, deletion, real RSS parsing over mocked HTTP, canonical URL deduplication, keyword semantics, failed source recovery, pending Slack retries, private DNS rejection, unsafe redirects and bounded bodies. Ruff checks and formatting are enforced alongside pytest in CI.
