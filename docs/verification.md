# Rebuild verification

Local rebuild checks and the public production launch were verified on 11 October 2026. The canonical live application is [subabot.gezici.me](https://subabot.gezici.me).

| Check | Result |
| --- | --- |
| Backend suite | Initial rebuild: 66 passed. Gateway extension: 73 passed, including proxy authentication in addition to authorization, workspace isolation, persistence, RSS parsing, deduplication, source failure recovery, SSRF controls, Slack retries, scheduler lifecycle and scan concurrency |
| Python lint and formatting | Ruff check and format checks pass |
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

Slack delivery is covered with mocked network responses. No real Slack messages were sent, and no production webhook has been configured. The rebuilt backend is healthy and the canonical production frontend passed the public smoke. Social posting was not performed. The local production preview is isolated from other projects.

A single production image request initially returned a temporary 503. The exact full live RSS flow passed on repeat, including image rendering. Safe fetch/render-stage diagnostics are included for future failures without logging watchlist contents, tokens or credentials.

The browser suite runs against the built server instead of a second Vite process. This avoids development dependency-cache interference and exercises the production code path. Each test creates its own disposable workspace and removes it afterward.

## Verified initial hosted release

- Both standalone Node and Vercel builds pass Astro checks with zero diagnostics.
- The first cloud preview exposed an adapter 11.0.13 startup failure caused by a missing Rolldown native binding. The exact 11.0.12 pin removes that runtime import. A copied, isolated function bundle passes dashboard GET/HEAD, all backend fetch paths, gateway header protection, canonical metadata, and bundled-font PNG rendering.
- The backend image was published for Linux AMD64 and ARM64 with the immutable digest recorded in `backend/helm/values.yaml`.
- The restored Helm chart passes strict lint, normal rendering, rendering with optional ingress/middleware disabled, and a complete live server dry-run against the installed schemas. These checks do not establish runtime health or persistent-volume readiness, and dry-run did not apply the chart.
- The approved legacy backup completed entirely inside the cluster: 45,056 bytes at `/data/legacy/database-before-rebuild.sqlite`, with integrity and restore verification. Temporary Job, ConfigMap, ServiceAccount, Role and RoleBinding resources were deleted.
- Argo is `Synced` and `Healthy` at `1d0c16841ef8870c5c791678023b6e77cd8393bf`. The backend Pod is 1/1 Ready with zero restarts. Public health returns 200, version 1.0.0, scheduler enabled; missing gateway authentication returns 401. The chart explicitly selects ServiceAccount `default` with token automount disabled, fixing inheritance of the pruned legacy account.
- [Hosted preview](https://subabot-fj4wuceac-dgtech.vercel.app), deployment `dpl_2Tpw9qPhnpTavWFhvBa6Dwi9TKoG`, passes the complete public smoke against that backend: one source and 19 real stories, saved state/search, isolation, public HTML and 1200 by 630 PNG, cloning, revocation, and deletion of both disposable workspaces with invalidated keys.
- Production deployment `dpl_45ktWJ4nTn6d9hTcardZ3FjsJ2DB` is ready from source `1d0c16841ef8870c5c791678023b6e77cd8393bf`, with `subabot.gezici.me` and `subabot.vercel.app` aliases assigned. The complete smoke passed again at the canonical production domain with 19 real stories and all disposable data cleaned up.
- The production homepage displays the new design. Preview browser checks verified desktop search plus the drawer and template flow at 390px width.
- The latest 69 backend log lines contained no `ERROR`, `Traceback`, or `CRITICAL`. The preview deployment's queried Vercel error/fatal logs were empty. These observations are limited to the checked windows.
- The same reusable smoke script also passed against the isolated Docker preview with 20 real stories.

Use [deployment.md](deployment.md) for the initial release identifiers, image digest, future release order, rollback, and public smoke command.

## Local preview

The isolated Docker Compose project is `subabot-rebuild-preview`, serving `http://localhost:4335`. The sample inbox is at `/dashboard?demo=1`. Its database is separate from the old project database and from test databases.

To stop this preview while preserving its data:

```sh
docker compose -p subabot-rebuild-preview stop
```

Run the normal deployment commands from the root README for a different domain or port. Read `docs/launch.md` before exposing the service publicly.
