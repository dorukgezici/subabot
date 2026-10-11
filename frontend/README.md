# Subabot frontend

Astro renders the landing page, template discovery, and public watchlists. React powers the private inbox. All browser API requests use the same-origin server proxy, keeping deployment details and Slack credentials off the client.

```sh
npm ci
npm run dev
```

Start the backend on port 8000 first. Open http://localhost:4321 or explore the independent sample workspace at http://localhost:4321/dashboard?demo=1.

Configuration: copy `.env.template` to `.env` if the defaults do not fit. `BACKEND_URL` and optional `BACKEND_PROXY_SECRET` are server-only. Set `PUBLIC_SITE_URL` to the public HTTPS origin before production build for canonical metadata. The frontend overwrites the gateway header from its own environment on every backend request.

```sh
npm run check
npm run build
npm start
```

Node 24 is the supported deployment runtime. Use `npm ci` with the committed lockfile.

Vercel sets `VERCEL=1`, selecting `@astrojs/vercel` with a 180-second function budget. The API proxy allows scans up to 130 seconds. The adapter is pinned to `11.0.12` because `11.0.13` produced a missing-native-binding startup failure in the deployed function. Docker and normal local builds use `@astrojs/node`; `npm start` is for that standalone output.

Deploy source through a remote Linux build. The social PNG renderer uses a native resvg dependency and a bundled DM Sans font, so a macOS-generated prebuilt function is unsuitable for Vercel. Exact canonical and Vercel deployment hostnames are trusted without a wildcard for other Vercel projects. See the [deployment runbook](../docs/deployment.md) for the existing project and release process.

`npm run test:e2e` builds first, then exercises the production Node server and an isolated backend through Playwright. Install Chromium once with `npx playwright install chromium`. Test ports default to 4330 and 8030 and can be overridden with `SUBABOT_TEST_FRONTEND_URL` and `SUBABOT_TEST_BACKEND_URL`.
