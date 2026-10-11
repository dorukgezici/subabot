#!/usr/bin/env node
// Node 22+. Runs against the public frontend's same-origin API proxy.
// Creates and removes two disposable workspaces. Never prints their recovery keys.
import { randomUUID } from "node:crypto";
import { setTimeout as delay } from "node:timers/promises";

const argument = process.argv[2];
if (argument === "--help" || argument === "-h") {
  console.log(
    "Usage: node scripts/verify-deployment.mjs https://subabot.example.com\n" +
      "Alternatively set SUBABOT_CHECK_ORIGIN. Optional SUBABOT_CHECK_CANONICAL_ORIGIN\n" +
      "sets the exact expected origin for canonical and social metadata, defaulting to the\n" +
      "request origin. All requests still use the request origin. Uses real public RSS, creates two disposable\n" +
      "workspaces, briefly publishes a watchlist, and deletes both workspaces on completion.\n" +
      "Does not connect Slack, send messages, or modify existing workspaces.",
  );
  process.exit(0);
}

function parseOrigin(input) {
  const value = new URL(input);
  if (
    !["http:", "https:"].includes(value.protocol) ||
    value.username ||
    value.password ||
    value.search ||
    value.hash ||
    value.pathname !== "/"
  ) {
    throw new Error("Invalid origin");
  }
  return value.origin;
}

let origin;
let canonicalOrigin;
try {
  origin = parseOrigin(argument || process.env.SUBABOT_CHECK_ORIGIN || "");
  canonicalOrigin = parseOrigin(
    process.env.SUBABOT_CHECK_CANONICAL_ORIGIN || origin,
  );
} catch {
  console.error(
    "Request and canonical origins must be HTTP(S) URLs without a path, query, credentials, or fragment. Use --help for details.",
  );
  process.exit(2);
}

const runId = randomUUID().slice(0, 8);
const workspaces = [];
const interrupt = new AbortController();
for (const signal of ["SIGINT", "SIGTERM"]) {
  process.once(signal, () => interrupt.abort());
}

function verify(condition, message) {
  if (!condition) throw new Error(message);
}

function safeError(error) {
  let message =
    error instanceof Error ? error.message : "Unknown verification error";
  for (const workspace of workspaces)
    message = message.replaceAll(workspace.token, "[redacted]");
  return message;
}

function metadataValue(html, tag, selector, value, attribute) {
  const matches = [];
  for (const match of html.matchAll(new RegExp(`<${tag}\\b[^>]*>`, "gi"))) {
    const attributes = Object.fromEntries(
      [...match[0].matchAll(/([\w:-]+)\s*=\s*(["'])(.*?)\2/g)].map((item) => [
        item[1].toLowerCase(),
        item[3],
      ]),
    );
    if (attributes[selector] === value) matches.push(attributes[attribute]);
  }
  verify(
    matches.length === 1,
    `Expected exactly one ${tag} ${selector}=${value} metadata element`,
  );
  return matches[0];
}

async function request(
  path,
  { token, method = "GET", body, expected = 200, cleanup = false } = {},
) {
  let response;
  try {
    response = await fetch(`${origin}${path}`, {
      method,
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      redirect: "error",
      signal: cleanup
        ? AbortSignal.timeout(20_000)
        : AbortSignal.any([
            interrupt.signal,
            AbortSignal.timeout(path === "/api/scan" ? 150_000 : 30_000),
          ]),
    });
  } catch {
    throw new Error(
      `${method} ${path}: network failure, timeout, interrupt, or unexpected redirect`,
    );
  }
  verify(
    response.status === expected,
    `${method} ${path}: expected HTTP ${expected}, received ${response.status}`,
  );
  return response;
}

async function api(path, options) {
  const response = await request(`/api${path}`, options);
  if (response.status === 204) return null;
  try {
    return await response.json();
  } catch {
    throw new Error(`${path}: expected a JSON response`);
  }
}

async function createWorkspace(label) {
  const result = await api("/workspaces", {
    method: "POST",
    body: { name: `Deployment verification ${label} ${runId}` },
    expected: 201,
  });
  verify(
    typeof result.token === "string" && result.token.length > 20,
    "Workspace creation did not return a recovery key",
  );
  // Register cleanup immediately, before any other assertion or request.
  const workspace = { token: result.token, id: result.workspace?.id };
  workspaces.push(workspace);
  verify(
    typeof workspace.id === "string",
    "Workspace creation did not return an ID",
  );
  return workspace;
}

async function cleanupWorkspace(workspace) {
  const deadline = Date.now() + 130_000;
  while (true) {
    try {
      await api("/workspace", {
        token: workspace.token,
        method: "DELETE",
        expected: 204,
        cleanup: true,
      });
      await request("/api/workspace", {
        token: workspace.token,
        expected: 401,
        cleanup: true,
      });
      return;
    } catch (error) {
      // A scan may still be settling after a network interruption. Retry only our own deletion.
      if (Date.now() >= deadline) throw error;
      await delay(5_000);
      const response = await fetch(`${origin}/api/workspace`, {
        headers: { Authorization: `Bearer ${workspace.token}` },
        signal: AbortSignal.timeout(20_000),
        redirect: "error",
      }).catch(() => null);
      if (response?.status === 401) return;
    }
  }
}

let result;
let failure;
try {
  console.log(`Verifying ${origin} with disposable workspaces.`);
  const health = await api("/health");
  verify(health.status === "ok", "API health check failed");
  const templates = await api("/templates");
  verify(
    Array.isArray(templates) && templates.length > 0,
    "Template catalog is empty",
  );
  await request("/");
  await request("/explore");
  await request("/dashboard");

  const owner = await createWorkspace("owner");
  const other = await createWorkspace("isolation");
  verify(
    owner.id !== other.id,
    "Workspace creation returned a reused workspace ID",
  );
  const monitor = await api("/monitors", {
    token: owner.token,
    method: "POST",
    expected: 201,
    body: {
      name: `Public deployment check ${runId}`,
      description:
        "Temporary automated verification of real RSS ingestion and public sharing.",
      keywords: [
        "a",
        "the",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "is",
        "AI",
        "Show HN",
        "React",
      ],
      // Use Hacker News' first-party endpoint, avoiding a third-party mirror dependency.
      feed_urls: ["https://news.ycombinator.com/rss"],
      match_mode: "any",
      public: false,
    },
  });
  console.log("Scanning a real public RSS feed.");
  const scan = await api("/scan", { token: owner.token, method: "POST" });
  verify(scan.checked > 0, "Scan did not check a feed");
  verify(
    Array.isArray(scan.errors) && scan.errors.length === 0,
    "Live RSS scan returned feed errors",
  );
  verify(scan.new_signals > 0, "Live RSS scan found no matching stories");
  const signals = await api("/signals", { token: owner.token });
  verify(
    Array.isArray(signals) && signals.length > 0,
    "Collected stories were not persisted",
  );
  const selected = signals.find(
    (signal) => typeof signal.title === "string" && signal.title.length > 0,
  );
  verify(
    selected && /^https?:\/\//.test(selected.url),
    "Collected story has an invalid title or URL",
  );
  await api(`/signals/${selected.id}`, {
    token: owner.token,
    method: "PATCH",
    body: { is_bookmarked: true, is_read: true },
  });
  const bookmarks = await api("/signals?bookmarked=true", {
    token: owner.token,
  });
  verify(
    bookmarks.some((signal) => signal.id === selected.id && signal.is_read),
    "Bookmark and read state did not persist",
  );
  const search = new URLSearchParams({ search: selected.title.slice(0, 100) });
  const matches = await api(`/signals?${search}`, { token: owner.token });
  verify(
    matches.some((signal) => signal.id === selected.id),
    "Search did not find the saved story",
  );
  const stats = await api("/workspace", { token: owner.token });
  verify(
    stats.stats.bookmarked === 1 && stats.stats.signals >= signals.length,
    "Workspace counts did not persist",
  );

  verify(
    (await api("/signals", { token: other.token })).length === 0,
    "Another workspace can list private stories",
  );
  verify(
    (await api("/monitors", { token: other.token })).length === 0,
    "Another workspace can list private monitors",
  );
  await request(`/api/monitors/${monitor.id}`, {
    token: other.token,
    method: "PATCH",
    body: { name: "Must not change" },
    expected: 404,
  });
  await request(`/api/signals/${selected.id}`, {
    token: other.token,
    method: "PATCH",
    body: { is_bookmarked: false },
    expected: 404,
  });
  await request("/api/workspace", { expected: 401 });

  const published = await api(`/monitors/${monitor.id}`, {
    token: owner.token,
    method: "PATCH",
    body: { public: true },
  });
  verify(
    typeof published.share_slug === "string" && published.share_slug.length > 0,
    "Publishing did not create a link",
  );
  const slug = encodeURIComponent(published.share_slug);
  const board = await api(`/public/${slug}`);
  verify(
    board.monitor.name === monitor.name && board.signals.length > 0,
    "Public API omitted the watchlist or stories",
  );
  const publicJson = JSON.stringify(board);
  verify(
    workspaces.every((workspace) => !publicJson.includes(workspace.token)),
    "Public data disclosed a recovery key",
  );
  verify(
    !publicJson.includes('"workspace_id"') &&
      !publicJson.includes('"webhook_url"'),
    "Public data disclosed private workspace fields",
  );
  verify(
    board.signals.every(
      (signal) => !("is_read" in signal) && !("is_bookmarked" in signal),
    ),
    "Public data disclosed private reading state",
  );
  const page = await request(`/s/${slug}`);
  const html = await page.text();
  verify(
    html.includes(monitor.name),
    "Public page did not render the watchlist title",
  );
  verify(
    html.includes(`/dashboard?clone=${slug}`),
    "Public page did not include the cloning entry point",
  );
  const canonicalPage = `${canonicalOrigin}/s/${slug}`;
  verify(
    metadataValue(html, "link", "rel", "canonical", "href") === canonicalPage,
    "Public page canonical URL does not match the expected origin and path",
  );
  verify(
    metadataValue(html, "meta", "property", "og:url", "content") ===
      canonicalPage,
    "Public page social URL does not match its canonical URL",
  );
  verify(
    metadataValue(html, "meta", "property", "og:image", "content") ===
      `${canonicalPage}/og.png`,
    "Public page social image URL does not match the expected origin and path",
  );
  const png = await request(`/s/${slug}/og.png`);
  verify(
    png.headers.get("content-type")?.startsWith("image/png"),
    "Social preview has the wrong content type",
  );
  const bytes = Buffer.from(await png.arrayBuffer());
  verify(
    bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])),
    "Social preview is not a PNG",
  );
  verify(
    bytes.length > 24 &&
      bytes.readUInt32BE(16) === 1200 &&
      bytes.readUInt32BE(20) === 630,
    "Social preview dimensions are incorrect",
  );

  // Match the dashboard's clone setup allowlist. Copying the source ID must not be necessary.
  const clonePayload = Object.fromEntries(
    [
      "name",
      "description",
      "keywords",
      "exclude_keywords",
      "match_mode",
      "feed_urls",
      "color",
    ].map((key) => [key, board.monitor[key]]),
  );
  clonePayload.public = false;
  clonePayload.enabled = false;
  const cloned = await api("/monitors", {
    token: other.token,
    method: "POST",
    body: clonePayload,
    expected: 201,
  });
  verify(
    cloned.id !== monitor.id && !cloned.public && !cloned.share_slug,
    "Cloning reused the source ID or public link",
  );
  verify(
    JSON.stringify(cloned.keywords) === JSON.stringify(board.monitor.keywords),
    "Cloning lost keyword rules",
  );
  verify(
    JSON.stringify(cloned.feed_urls) ===
      JSON.stringify(board.monitor.feed_urls),
    "Cloning lost feed sources",
  );

  await api(`/monitors/${monitor.id}`, {
    token: owner.token,
    method: "PATCH",
    body: { public: false },
  });
  await request(`/api/public/${slug}`, { expected: 404 });
  await request(`/s/${slug}`, { expected: 404 });
  await request(`/s/${slug}/og.png`, { expected: 404 });
  result = {
    origin,
    canonicalOrigin,
    realSourcesChecked: scan.checked,
    realSignalsCollected: scan.new_signals,
    bookmarkAndSearch: "passed",
    workspaceIsolation: "passed",
    publicPageAndPng: "passed",
    cloneSetup: "passed",
    revocation: "passed",
  };
} catch (error) {
  failure = safeError(error);
} finally {
  const outcomes = await Promise.allSettled(workspaces.map(cleanupWorkspace));
  const failures = outcomes.filter((outcome) => outcome.status === "rejected");
  if (failures.length) {
    console.error(
      `Cleanup failed for ${failures.length} disposable workspace(s). Their keys were not printed.`,
    );
    for (const outcome of failures) console.error(safeError(outcome.reason));
    failure ||= "Disposable workspace cleanup did not finish";
  } else if (workspaces.length) {
    console.log(
      `Deleted all ${workspaces.length} disposable workspaces and confirmed their keys are invalid.`,
    );
  }
}

if (failure) {
  console.error(`Verification failed: ${failure}`);
  process.exitCode = 1;
} else {
  console.log(JSON.stringify({ ...result, cleanup: "passed" }, null, 2));
}
