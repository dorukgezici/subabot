# Subabot launch and growth plan

The product promise is simple: follow the ideas that matter without following every feed. The first useful moment is a relevant story in a personal watchlist. The sharing loop starts after that moment, when the user has something worth passing on.

## Product loop already implemented

1. A visitor sees the product and example signals on the landing page.
2. They choose a curated watchlist or create one from their own feeds and keywords.
3. They see matching stories, then bookmark, refine, or connect Slack.
4. They choose to make a useful watchlist public.
5. A reader opens its public page with a clear title, keywords, live stories, and social preview.
6. The reader clones the watchlist into their own private workspace.

The creator attribution is deliberately visible on public pages and social cards. It gives Doruk a natural connection to useful work. Sharing is opt-in, and no message is sent to a user's contacts automatically.

## Pick a narrow first audience

Start with people who already spend time assembling a daily reading list: developers following AI tools, open-source maintainers, and technical founders. The available feeds make these use cases easy to demonstrate. Avoid positioning Subabot as comprehensive brand or social listening because RSS coverage cannot support that claim.

Create three public watchlists with distinct jobs, for example:

- AI tools worth trying: practical releases and developer tools, with exclusions for topics that generate noise.
- Open-source radar: relevant repository news and engineering blogs.
- Founder reading list: lessons, launches, and technical business stories from a small set of high-quality sources.

Validate every source and read the first results before sharing. A narrow watchlist with consistently useful matches is more valuable than a broad list with a large source count.

## Suggested launch sequence

These are drafts and tasks for a human launch. No outreach, social posting, email, or community submission is automated by this repository.

1. Publish a short product walkthrough from Doruk's account showing a real watchlist going from setup to one useful match. Include the public watchlist URL and the repository.
2. Write a concise build story explaining what was rebuilt, why feeds still matter, and what Subabot intentionally does. Show real UI screenshots and a useful finding.
3. Share a relevant watchlist in one community where Doruk already participates, following that community's self-promotion rules. Ask for missing sources rather than asking for generic engagement.
4. Turn good source suggestions into better watchlists. Credit contributors where appropriate and invited.
5. Publish one useful result each week with the watchlist link. Let the result earn attention for the product.
6. Submit the project to a suitable launch or developer directory once onboarding, public previews, and live scans are verified on the production domain.

Use real examples and results. Do not fabricate usage counts, testimonials, rankings, or AI capabilities. Virality is an outcome to test, not a product promise.

## Measurement without a tracking dependency

The application has no third-party analytics requirement. Before adding tracking, choose a small set of events and avoid collecting story contents, feed URLs, keywords, recovery tokens, or Slack webhook secrets.

Recommended event names and safe properties for a future first-party implementation:

| Event                     | Safe properties                          | Decision it supports                        |
| ------------------------- | ---------------------------------------- | ------------------------------------------- |
| `workspace_created`       | Entry path, selected template ID         | Which entry points help people start?       |
| `monitor_created`         | Template ID, source count, keyword count | Is setup simple enough?                     |
| `first_signal_found`      | Minutes since watchlist creation         | How quickly does the product deliver value? |
| `monitor_shared`          | Signal count                             | Do users find results worth sharing?        |
| `shared_watchlist_viewed` | Public share slug, referring domain      | Which watchlists are useful to others?      |
| `watchlist_cloned`        | Public share slug                        | Do readers want their own version?          |

These events are a measurement plan, not an assertion that instrumentation already exists. Early feedback can be reviewed manually. Useful initial metrics are time to first useful result, percentage of watchlists with at least one match, share-page-to-clone conversion, and returning workspaces. Visitor volume by itself is not proof of product value.

## Production launch checklist

- [ ] Configure the production domain, HTTPS, and `PUBLIC_SITE_URL` consistently on frontend and backend.
- [ ] Put the frontend behind a reverse proxy. Keep the backend port private and use one scheduler process. Only enable `SUBABOT_TRUST_PROXY_CLIENT_IP` behind the trusted frontend proxy, as Compose does.
- [ ] Persist the SQLite database on a durable volume and test a restore from backup.
- [ ] Confirm the hosting environment can resolve and fetch the chosen public feeds.
- [ ] Set request rate limits at the public ingress, including workspace creation and public image generation. Application limits do not replace a shared ingress limit at scale.
- [ ] Check application logs for errors without logging recovery tokens, authorization headers, or webhook URLs.
- [ ] Create a new workspace in a clean browser, configure a watchlist, run a scan, and confirm a real feed match appears.
- [ ] Save a recovery key, restore it in a second browser, and confirm it opens the same workspace.
- [ ] Verify a second independent workspace cannot see the first workspace's private content.
- [ ] Test read, unread, bookmarks, search, source editing, and a no-match state.
- [ ] Connect a test Slack webhook, trigger a matching story, and verify one notification arrives without repeating on the next scan.
- [ ] Enable sharing, open the public URL in a private browser, inspect the PNG preview, and clone the watchlist.
- [ ] Disable sharing and verify that both the public page and its PNG preview return 404. Existing third-party preview caches may retain content.
- [ ] Confirm the public URL never includes a workspace token and that no Slack webhook or personal read/bookmark state appears in its response.
- [ ] Check mobile navigation, keyboard focus, empty states, API failure states, and long watchlist names.
- [ ] Verify `/robots.txt`, `/sitemap.xml`, canonical URLs, page descriptions, and social previews use the public domain.
- [ ] Replace example policies or contact details if the operator's deployment requires changes.
- [ ] Run frontend checks, backend tests, and both Docker builds in CI.

## Backups and recovery

The default Compose deployment keeps the SQLite database in the `subabot-data` named volume. Prefer a SQLite-aware backup or stop the backend briefly before copying the database files. Store backups outside the host and confirm restoration on a separate instance. Back up any SQLite journal files consistently with the database, rather than copying a live database file in isolation.

Workspace recovery is capability based. There is no server-side password reset or email recovery. Operators should make the recovery-key UX clear and avoid suggesting that a lost token can be recovered automatically.

## Current operating limits

The scheduler checks on a configurable cadence, 15 minutes by default. Feeds vary in availability, published history, update frequency, and quality. The app has limits on watchlists, URLs, request sizes, and manual scan frequency. A new watchlist can have no matches even when working correctly. Slack is optional and depends on a valid incoming webhook.

SQLite and the in-process scheduler are appropriate for a small deployment with one backend process. Before horizontal scaling, move scheduled work to one dedicated worker, use shared rate limiting and coordination, and evaluate database contention under actual load. Do not run independent pollers against the same data and assume notification delivery will remain coordinated.

## Upgrade references

The rewrite removes the old Prefect deployment and Tailscale CI dependency. Workflow versions were checked against their official release notes on 2026-10-11:

- [GitHub checkout releases](https://github.com/actions/checkout/releases): use v7, which includes safer pull-request checkout behavior and current dependency fixes.
- [GitHub setup-node releases](https://github.com/actions/setup-node/releases): use v7 with Node.js 24 for the frontend.
- [Astral setup-uv releases](https://github.com/astral-sh/setup-uv/releases): pin v10.3.0 to its immutable commit with Python 3.14 for backend checks. The v10 major-version alias is not published.
- [resvg rendering API](https://github.com/thx/resvg-js/blob/main/index.d.ts): public social previews render PNG images on the server with system fonts available in the Docker image.

Application dependency upgrade details and API behavior are documented in the backend and frontend source and their lockfiles.
