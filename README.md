# Subabot

**Less noise. More signal.** An open-source RSS radar for the things you care about, built by [Doruk Gezici](https://github.com/dorukgezici).

Follow keywords across your favorite feeds, read the matches in a calm inbox, and send new discoveries to Slack. Start with a curated watchlist, or build one for your corner of the internet. Make a watchlist public when it is useful to others, and let anyone create their own copy.

## What you can do

- Create a private workspace without an account or third-party login.
- Follow RSS and Atom feeds with keyword, exclusion, and any/all matching rules.
- Scan on demand, or let the backend check for new matches on a schedule.
- Read, search, bookmark, and filter matching stories in one inbox.
- Connect an optional Slack incoming webhook for new matches.
- Share a public watchlist with a preview image and a one-click clone link.
- Start from curated watchlist templates on `/explore`.

Subabot monitors public feeds, not the whole web. It does not scrape social networks, access private sites, or classify stories with an AI model. Stories appear when they are present in a configured feed and match your rules.

## Run it with Docker

Install Docker with Compose, then run from the repository root:

```sh
docker compose up --build -d
```

Open [localhost:4321](http://localhost:4321). The frontend proxies API calls to the backend. Only the frontend port is published. SQLite data persists in the `subabot-data` Docker volume, and the scheduler runs every 15 minutes by default.

```sh
docker compose logs -f
docker compose down
```

`docker compose down` keeps the database volume. Adding `--volumes` deletes it.

For a separate self-hosted Compose deployment, put an HTTPS reverse proxy in front of port 4321 and set the canonical site URL before building:

```sh
PUBLIC_SITE_URL=https://subabot.example.com docker compose up --build -d
```

The published port binds to `127.0.0.1` by default. Set `SUBABOT_BIND_ADDRESS=0.0.0.0` only when the network configuration requires it. Run one backend process so that one scheduler owns feed polling. Compose enables trusted client-IP forwarding from the frontend proxy; keep the backend private when using this setting. See [the launch checklist](docs/launch.md) before exposing an instance publicly.

## Local development

Requirements: Node.js 24, Python 3.14, and [uv](https://docs.astral.sh/uv/).

Backend:

```sh
cd backend
uv sync
uv run start
```

Frontend, in another terminal:

```sh
cd frontend
npm ci
npm run dev
```

The frontend runs on port 4321 and connects to `http://127.0.0.1:8000` by default. Set `BACKEND_URL` on the frontend server to change that address. `PUBLIC_SITE_URL` controls canonical URLs, social previews, robots.txt, and the sitemap. See [backend configuration](backend/README.md) for feed limits, scheduling, and storage settings.

## Architecture

| Layer                 | Implementation                                                              |
| --------------------- | --------------------------------------------------------------------------- |
| Pages and SEO         | Astro with Vercel Functions in production; Node standalone locally           |
| Interactive workspace | React and TypeScript                                                        |
| API                   | FastAPI and Pydantic                                                        |
| Data                  | SQLModel with SQLite                                                        |
| Feed ingestion        | Bounded HTTP fetching, RSS/Atom parsing, keyword rules, deduplication       |
| Notifications         | Optional Slack incoming webhooks                                            |
| Operations            | Vercel frontend; k3s, Argo CD and Longhorn backend; Compose for local use      |

The frontend is a server application because public watchlists, public social images, and the API proxy are dynamic. The Vercel adapter is selected by `VERCEL=1`; other builds retain the standalone Node adapter. The backend needs persistent storage and one always-running scheduler process. No Supabase, Prefect, Slack OAuth app, or paid AI provider is required. The existing cluster uses Tailscale for operator access, while application users connect through HTTPS.

## Public hosting

The prepared deployment targets are `https://subabot.gezici.me` for the Vercel frontend and `https://subabot.pub.gezici.me` for the persistent backend. The backend's Helm chart preserves its existing ingress and pins an immutable image digest. A server-only shared gateway key protects API access between the two hosts.

Read the [deployment runbook](docs/deployment.md) for the current rollout checkpoint, required secret configuration, backup boundary, staged release, smoke checks, and rollback procedure. Preparation is not a declaration that the rebuilt production service is live.

## Workspace privacy

Each workspace has a secret capability token stored in your browser. It grants access to that workspace, so treat any exported recovery key like a password. There is no email recovery flow. Clearing browser storage without saving the recovery key can leave you unable to open the workspace again.

Watchlists start private. Enabling sharing makes that watchlist's name, description, keywords, feed sources, and matched stories accessible through its public link. Slack webhook credentials and personal read/bookmark state are not included. Public links are public even when they are hard to guess. Disable sharing to stop serving a public watchlist. Third-party social preview caches may retain an earlier preview.

## Checks

```sh
cd frontend
npm run check
npm run build
npx playwright install chromium
npm run test:e2e
```

The browser tests start isolated services on ports 4330 and 8030, or reuse existing services there during local development. They cover monitor persistence, demo interactions, public sharing and cloning, workspace recovery, and mobile template discovery. Set `SUBABOT_TEST_FRONTEND_URL` and `SUBABOT_TEST_BACKEND_URL` to use different local ports.

```sh
cd backend
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

GitHub Actions runs frontend checks, backend linting and tests, and Docker builds on pull requests and changes to `main`. The container workflow can publish commit-tagged backend images through its explicit `publish_backend` dispatch input. Vercel Git integration and the existing Argo CD application provide deployment automation separately, so merging the tracked branch can trigger a release. Follow the deployment runbook before merging infrastructure changes.

## Build in public

Useful watchlists are the distribution loop: create something worth following, share its public page, and let readers clone it. Public pages link back to Subabot and its creator. The [launch plan](docs/launch.md) covers a practical initial audience, publishing sequence, and outcome metrics without claiming growth is guaranteed.

Contributions are welcome. Open an issue with a concrete feed example, reproduction steps, or a focused proposal.

## License

[GNU Lesser General Public License v3.0](LICENSE).

See [frontend migration notes](docs/frontend-migration.md) for the Astro/React upgrade decisions and [backend migration notes](backend/MIGRATION.md) for the changelog review.
