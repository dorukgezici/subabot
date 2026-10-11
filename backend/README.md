# Subabot API

A FastAPI service that turns public RSS and Atom feeds into a private, searchable signal inbox. Every workspace owns its monitors, saved stories and optional Slack connection. There are no required external services or credentials.

## Run locally

Install Python 3.14 and [uv](https://docs.astral.sh/uv/). From this directory:

```sh
uv sync --frozen
uv run start
```

The API is at `http://localhost:8000/api`, interactive API docs at `http://localhost:8000/docs`, and health at `http://localhost:8000/api/health`. For development reload use `uv run uvicorn subabot.api:app --reload`. The Astro frontend uses port 4321 and proxies requests to this service.

Existing `.env` files are deliberately not loaded. Defaults work immediately. To override them, copy `.env.template` to a new file such as `.env.local` and run `uv run --env-file .env.local start`. Keep the old project's `.env` untouched until you have separately retired any credentials it contains.

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Tests use isolated temporary SQLite databases, mocked feed HTTP and mocked Slack delivery. No test requires internet or sends messages.

## Workspace access

`POST /api/workspaces` with `{"name":"My studio"}` returns a private `token` and `workspace`. Send `Authorization: Bearer <token>` for private requests. The browser keeps the token in local storage. The database stores only a SHA-256 hash. Save the recovery key before clearing browser storage or switching devices. Anyone with the key controls the workspace; there is no email account or password recovery. Public links never contain it.

`DELETE /api/workspace` deletes the workspace, monitors, signals and saved webhook. It also invalidates the recovery key and every public board. It returns 409 if a scan is currently running, so deletion cannot race with new writes.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Public health and scheduler status |
| `GET /api/templates` | Public starter templates as an array |
| `GET`, `PATCH`, `DELETE /api/workspace` | Workspace details, name and deletion |
| `GET`, `POST /api/monitors` | List and create monitors |
| `PATCH`, `DELETE /api/monitors/{id}` | Edit, pause, publish or delete a monitor |
| `POST /api/monitors/from-template/{id}` | Create from a template; optional `{"name":"..."}` |
| `POST /api/monitors/{id}/publish` | Publish explicitly and generate a share slug |
| `GET /api/signals` | Inbox; filters `monitor_id`, `bookmarked`, `unread`, `search`, `limit`, `offset` |
| `PATCH /api/signals/{id}` | Set `is_read` and/or `is_bookmarked` |
| `POST /api/scan` | Scan active monitors and retry pending Slack delivery |
| `POST`, `DELETE /api/integrations/slack` | Save or disconnect an incoming webhook |
| `GET /api/public/{slug}` | Public board with disclosed settings and recent stories |

List routes return arrays. Dates are ISO 8601 UTC. API errors use `detail`, with field validation errors as an array. The OpenAPI document describes exact request schemas.

## Matching and delivery

Keywords match article titles and descriptions without regard to case, using word boundaries so `AI` does not match `paid`. `any` needs one keyword; `all` needs every keyword. Any excluded keyword rejects the article. RSS and Atom are supported. Feed HTML becomes plain text. Tracking parameters are removed from article links; `(monitor_id, canonical URL hash)` is uniquely constrained in SQLite, so repeated scans and duplicate sources do not create repeated signals. The same article can intentionally appear in different monitors.

The first scan imports up to 100 currently available entries from each feed. This is not a historical archive of entries that have already left the source feed. One failed feed does not cancel successful feeds. Each monitor records its last check and a safe `last_error` summary, so scheduled failures remain visible.

To connect Slack, create an [incoming webhook](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/) for the target channel and paste its URL in Settings. Saving validates the URL and does not send a test message. Only new matches discovered while connected enter the delivery queue. Previously collected stories are not sent on connection. Delivery is paced at roughly one message per second, up to 20 per scan. Failed deliveries remain pending and retry on a future scan; paused monitors do not deliver. Disconnecting clears the queue. Message content uses plain text blocks to prevent feed text from triggering mentions.

Webhook delivery is at least once: an interrupted process after Slack accepts a message but before the database commit can produce a duplicate on retry. Webhooks do not provide an idempotency key. The UI connection status means a webhook was saved, not that Slack has accepted a message. Actual delivery failures are returned in scan results.

Publishing discloses a monitor's name, description, keywords, exclusion rules, feed URLs and latest 100 matching stories. Read/bookmark state, workspace details, webhook and recovery key remain private. Unpublishing revokes its URL immediately. Republishing generates a new URL.

## Configuration and operation

| Variable | Default | Purpose |
| --- | --- | --- |
| `SUBABOT_DATABASE_URL` | `sqlite:///./subabot.db` | Persistent database; use a Docker volume |
| `SUBABOT_FRONTEND_URL` | `http://localhost:4321` | The one allowed CORS origin |
| `SUBABOT_SCHEDULER_ENABLED` | `true` | Scan enabled monitors automatically |
| `SUBABOT_SCAN_INTERVAL_SECONDS` | `900` | Scheduler delay, minimum 60 seconds |
| `SUBABOT_SCAN_COOLDOWN_SECONDS` | `15` | Delay before a manual rescan |
| `SUBABOT_FEED_TIMEOUT_SECONDS` | `12` | Whole feed request deadline, including redirects |
| `SUBABOT_MAX_FEED_BYTES` | `2000000` | Maximum feed response size |
| `SUBABOT_MAX_MONITORS` | `25` | Per-workspace monitor limit |
| `SUBABOT_TRUST_PROXY_CLIENT_IP` | `false` | Trust `x-subabot-client-address` from a private or secret-authenticated frontend proxy |
| `SUBABOT_PROXY_SHARED_SECRET` | empty | Require this server-only secret in `x-subabot-proxy-secret` for API access, except `/api/health` |

Run one API worker and one replica with this SQLite deployment. The scheduler, scan exclusion and IP limits live in that process. SQLite enables WAL, foreign keys and a busy timeout. For multiple replicas, introduce a shared queue, shared rate limiter and coordinated scheduler, then migrate storage before scaling. Scheduler timing is interval plus the duration of preceding scans; it is not an exact delivery guarantee. Default storage grows with collected signals, so monitor disk use and back up the database.

Each workspace can define 20 included and 20 excluded keywords per monitor, 10 feeds per monitor, and up to 25 monitors. Feed polling uses at most six concurrent requests per workspace and three scans globally. A scan has a 120 second deadline. Inbox pages contain at most 200 stories, default 100; use `offset` for pagination. Request bodies are limited to 32 KB, including chunked bodies. New workspaces are limited to 20 per hour per client IP in a single process. In the Docker deployment, only the frontend is public and the backend trusts its explicitly overwritten client-address header. For a backend exposed over the public internet, configure `SUBABOT_PROXY_SHARED_SECRET` before enabling that trust setting.

When frontend and backend run on different hosting providers, generate a strong random secret and set the same value in the backend's `SUBABOT_PROXY_SHARED_SECRET` and the frontend's server-only `BACKEND_PROXY_SECRET`. The frontend must attach `x-subabot-proxy-secret` to every backend request and overwrite the client-address header itself. The backend uses a constant-time comparison before routing requests or updating rate limits. Invalid or absent secrets return 401, while `/api/health` remains public for probes. Workspace authorization still requires its separate bearer token. Keep the shared secret out of browser bundles, URLs, logs, public configuration and source control. Use HTTPS between hosts. An empty shared secret preserves local and private-network operation.

Outbound feed requests allow only public HTTP/S addresses on ports 80 and 443. A custom DNS resolver validates every returned address and the connector connects to those exact addresses; redirects are revalidated. Loopback, private, reserved and metadata addresses are blocked, as are user credentials and proxy environment variables. Responses request identity encoding and reject unsolicited compression, preventing decompression bombs from bypassing the size cap. The deployment still benefits from an outbound network policy as an additional boundary.

Serve production traffic over HTTPS and keep the API behind the frontend proxy. Webhook secrets are stored in the SQLite database and never returned in API responses or validation errors. Restrict and encrypt the database volume and backups. Browser recovery keys are sensitive, so maintain the frontend's script policy and avoid third-party scripts. Public board publishing is explicit. There are no tracking pixels or automatic marketing messages.

## Container

```sh
docker build -t subabot-api .
docker run --rm -p 8000:8000 -v subabot-data:/data subabot-api
```

The container runs as a non-root user and keeps data under `/data`. Use Compose for the complete local stack. The existing hosted setup uses the [Helm chart](helm/README.md), with one k3s replica, an immutable image digest, a retained Longhorn PVC, and a secret-authenticated Vercel gateway. Follow the [deployment runbook](../docs/deployment.md) for the staged Argo CD rollout and rollback. See [MIGRATION.md](MIGRATION.md) for dependency and architecture upgrade decisions.
