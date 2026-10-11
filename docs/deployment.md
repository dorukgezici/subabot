# Public deployment

## Hosting targets

The existing Subabot Vercel project in the DGtech team serves `https://subabot.gezici.me`. Its root directory is `frontend`, with Node 24, `npm ci`, and `npm run build`. Vercel builds use the Vercel adapter; Docker and local development retain the standalone Node adapter.

The Vercel adapter is pinned to `11.0.12`. Version `11.0.13` produced a function that imported the build-time Rolldown native binding and failed during cloud startup. The pinned version passes isolated function-bundle checks, including dashboard GET/HEAD and social PNG generation. Recheck an isolated Linux bundle before upgrading this dependency.

The persistent backend target is `https://subabot.pub.gezici.me` on the existing Kubernetes infrastructure. Do not move the SQLite database or in-process scheduler into an ephemeral function.

The production domain still serves the old release until the backend rollout and public verification are complete. Deployment preparation is on `codex/public-launch`.

## Published backend artifact

The reviewed backend is available for both Linux AMD64 and ARM64:

```text
docker.io/dorukgezici/subabot:v2-d6a0e28710cabd1fb6bb1c245e6ff935ebea90ba
docker.io/dorukgezici/subabot@sha256:15a3bc34f63b2c0b2dda963f76c664e7516f15d67f507f1a9a402824962bef21
```

The [container build and publication](https://github.com/dorukgezici/subabot/actions/runs/38097644184) passed. Future releases can run `backend-build.yml` with the `publish_backend` input enabled. Images receive a commit-specific tag; the old `latest` image is not overwritten.

## Backend rollout

Deploy one backend replica and one worker with a persistent volume mounted at `/data`, writable by UID 10001. Use a fresh `subabot.db` for this application. The old application database has a different schema and must remain preserved.

Required environment:

```text
SUBABOT_DATABASE_URL=sqlite:////data/subabot.db
SUBABOT_FRONTEND_URL=https://subabot.gezici.me
SUBABOT_SCHEDULER_ENABLED=true
SUBABOT_TRUST_PROXY_CLIENT_IP=true
SUBABOT_SCAN_INTERVAL_SECONDS=900
```

Generate a strong shared gateway secret directly into the hosting secret stores. Configure it as `SUBABOT_PROXY_SHARED_SECRET` on the backend and `BACKEND_PROXY_SECRET` in Vercel. Do not commit or log it. The public backend requires this secret for all API requests except `/api/health`, so browsers cannot bypass the frontend's trusted client-address handling.

Keep the previous deployment available until the new replica is healthy. Configure the public ingress to allow scan requests lasting at least 130 seconds, and retain HTTPS. Verify a SQLite-aware backup and restoration before directing the production app to the new service.

## Frontend rollout

These variables have been configured in Vercel for production and preview:

```text
PUBLIC_SITE_URL=https://subabot.gezici.me
BACKEND_URL=https://subabot.pub.gezici.me
```

`BACKEND_PROXY_SECRET` must also be configured before releasing the protected backend. Keep Vercel's automatic system environment variables enabled, including `VERCEL`, so the cloud adapter is selected. Deploy source through a remote Linux build, since social-image rendering has a native dependency. Do not publish a macOS prebuilt function bundle.

After backend verification, deploy the reviewed source to production and check the canonical domain. Test workspace creation, a real feed scan, recovery, sharing, cloning, social PNG rendering, and revocation through the public origin. Check `/api/health`, `/robots.txt`, `/sitemap.xml`, canonical URLs, and runtime logs as part of that verification.

## Current access dependency

The configured cluster management endpoint is on the existing private Tailscale network. Tailscale was disconnected during this deployment attempt. Automatic approval review required explicit user approval before reconnecting this Mac. No VPN connection, cluster mutation, or production release was performed while that approval was pending.
