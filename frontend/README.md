# Subabot frontend

Astro renders the landing page, template discovery, and public watchlists. React powers the private inbox. All browser API requests use the same-origin server proxy, keeping deployment details and Slack credentials off the client.

```sh
npm ci
npm run dev
```

Start the backend on port 8000 first. Open http://localhost:4321 or explore the independent sample workspace at http://localhost:4321/dashboard?demo=1.

Configuration: copy `.env.template` to `.env` if the defaults do not fit. `BACKEND_URL` is server-only. Set `PUBLIC_SITE_URL` to the public HTTPS origin before production build for canonical metadata.

```sh
npm run check
npm run build
npm start
```

Node 24 is the supported deployment runtime. Use `npm ci` with the committed lockfile.

`npm run test:e2e` builds first, then exercises the production Node server and an isolated backend through Playwright. Install Chromium once with `npx playwright install chromium`. Test ports default to 4330 and 8030 and can be overridden with `SUBABOT_TEST_FRONTEND_URL` and `SUBABOT_TEST_BACKEND_URL`.
