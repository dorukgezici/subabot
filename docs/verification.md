# Rebuild verification

Verified locally on 11 October 2026.

| Check | Result |
| --- | --- |
| Backend suite | 66 passed, including authorization, workspace isolation, persistence, RSS parsing, deduplication, source failure recovery, SSRF controls, Slack retries, scheduler lifecycle and scan concurrency |
| Python lint and formatting | Ruff check passes; 19 Python files pass format check |
| Frontend | Astro type checking and production build pass |
| Production browser suite | 5 passed against freshly started built Node server and isolated FastAPI database |
| Browser flows | Monitor create/edit/pause/delete and reload persistence; sample inbox search/save/read; publish/clone/revoke with owner isolation; recovery export/restore; mobile template discovery |
| Public metadata | SSR title, canonical metadata, escaped names and 1200x630 PNG generation checked; page and image return 404 after revocation |
| Live source verification | All 8 unique starter RSS source URLs fetched and parsed successfully |
| Live product flow | Real Hacker News RSS scan collected 9 matching stories, bookmark persisted, public page and PNG rendered, unpublishing revoked access |
| Request bounds | Oversized frontend proxy request returns 413 before unbounded buffering |
| Deployment | Both production Docker images build and run as non-root users; Compose services pass health checks; backend port stays private; database lives on a persistent volume |
| Responsive design | Landing checked from 320px to 1440px without horizontal overflow; Explore header checked at 320px; desktop/mobile dashboard screenshots captured |
| Accessibility | Native dialog labels and Escape behavior; mobile drawer focus, Tab containment and restoration; visible keyboard focus; reduced-motion behavior; no-JavaScript marketing content |
| Repository | git diff --check passes; authored source and documents contain no em dash characters |

## Useful distinctions

Slack delivery is covered with mocked network responses. No real Slack messages were sent, and no production webhook has been configured. Public deployment and social posting were not performed. The local production preview is isolated from other projects.

A single production image request initially returned a temporary 503. The exact full live RSS flow passed on repeat, including image rendering. Safe fetch/render-stage diagnostics are included for future failures without logging watchlist contents, tokens or credentials.

The browser suite runs against the built server instead of a second Vite process. This avoids development dependency-cache interference and exercises the production code path. Each test creates its own disposable workspace and removes it afterward.

## Local preview

The isolated Docker Compose project is `subabot-rebuild-preview`, serving `http://localhost:4335`. The sample inbox is at `/dashboard?demo=1`. Its database is separate from the old project database and from test databases.

To stop this preview while preserving its data:

```sh
docker compose -p subabot-rebuild-preview stop
```

Run the normal deployment commands from the root README for a different domain or port. Read `docs/launch.md` before exposing the service publicly.
