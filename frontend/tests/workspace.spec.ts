import {
  test,
  expect,
  type APIRequestContext,
  type Page,
} from "@playwright/test";
import { readFile } from "node:fs/promises";

const TOKEN_KEY = "subabot.workspace.v1";
const createdTokens = new Set<string>();
const authorization = (token: string) => ({ Authorization: `Bearer ${token}` });

async function openWorkspace(page: Page) {
  await page.goto("/dashboard");
  await expect(
    page.getByRole("heading", { name: "What are you curious about?" }),
  ).toBeVisible();
  const token = await page.evaluate(
    (key) => localStorage.getItem(key),
    TOKEN_KEY,
  );
  expect(token).toBeTruthy();
  createdTokens.add(token!);
  return token!;
}

async function createMonitor(page: Page, name: string) {
  await page.getByRole("button", { name: "New monitor", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog
    .getByRole("textbox", { name: "Monitor name", exact: true })
    .fill(name);
  await dialog.getByRole("textbox", { name: /^Keywords/ }).fill("Astro, React");
  await dialog
    .getByRole("textbox", { name: /^RSS feeds/ })
    .fill("https://hnrss.org/frontpage");
  await dialog
    .getByRole("button", { name: "Create monitor", exact: true })
    .click();
  await expect(dialog).toBeHidden();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  return page
    .locator(".monitor-card")
    .filter({ has: page.getByRole("heading", { name, exact: true }) });
}

async function monitors(request: APIRequestContext, token: string) {
  const response = await request.get("/api/monitors", {
    headers: authorization(token),
  });
  expect(response.ok()).toBeTruthy();
  return response.json() as Promise<
    Array<{
      id: string;
      name: string;
      enabled: boolean;
      public: boolean;
      share_slug: string | null;
      keywords: string[];
      feed_urls: string[];
    }>
  >;
}

test.afterEach(async ({ request }) => {
  for (const token of createdTokens)
    await request.delete("/api/workspace", { headers: authorization(token) });
  createdTokens.clear();
});

test("a new workspace can create, edit, pause, persist, and delete a monitor", async ({
  page,
  request,
}) => {
  const token = await openWorkspace(page);
  let card = await createMonitor(page, "E2E frontend radar");
  expect((await monitors(request, token))[0].keywords).toEqual([
    "astro",
    "react",
  ]);

  await card.getByRole("button", { name: "Edit", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("textbox", { name: "Monitor name", exact: true })
    .fill("E2E edited radar");
  await page.getByRole("button", { name: "Save changes", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeHidden();
  card = page.locator(".monitor-card").filter({
    has: page.getByRole("heading", { name: "E2E edited radar", exact: true }),
  });
  await card.getByRole("checkbox", { name: "Pause E2E edited radar" }).click();
  await expect(card.getByText("Paused", { exact: true })).toBeVisible();

  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Your signal inbox" }),
  ).toBeVisible();
  await page
    .getByRole("navigation", { name: "Workspace", exact: true })
    .getByRole("button", { name: /^Monitors/ })
    .click();
  await expect(
    card.getByRole("checkbox", { name: "Resume E2E edited radar" }),
  ).not.toBeChecked();
  const persisted = await monitors(request, token);
  expect(persisted).toHaveLength(1);
  expect(persisted[0].name).toBe("E2E edited radar");
  expect(persisted[0].enabled).toBe(false);

  page.once("dialog", (dialog) => dialog.accept());
  await card.getByRole("button", { name: "Delete E2E edited radar" }).click();
  await expect(
    page.getByRole("heading", { name: "A home for your curiosity." }),
  ).toBeVisible();
  expect(await monitors(request, token)).toHaveLength(0);
});

test("sample signals can be searched, bookmarked, and marked read without creating a workspace", async ({
  page,
}) => {
  await page.goto("/dashboard?demo=1");
  await expect(
    page.getByText("Interactive demo", { exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate((key) => localStorage.getItem(key), TOKEN_KEY),
  ).toBeNull();
  const search = page.getByRole("textbox", { name: "Search signals" });
  await search.fill("smaller model");
  const article = page.locator(".signal-card");
  await expect(article).toHaveCount(1);
  await article
    .getByRole("button", { name: "Save signal", exact: true })
    .click();
  await expect(
    article.getByRole("button", { name: "Unsave signal", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await article
    .getByRole("button", { name: "Mark as read", exact: true })
    .click();
  await expect(
    article.getByRole("button", { name: "Mark as unread", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: /^Unread/ }).click();
  await expect(
    page.getByRole("heading", { name: "No signals found." }),
  ).toBeVisible();
  await page
    .getByRole("navigation", { name: "Workspace", exact: true })
    .getByRole("button", { name: /^Saved signals/ })
    .click();
  await expect(page.locator(".signal-card")).toHaveCount(2);
  await expect(
    page.getByRole("heading", {
      name: "A smaller model. A bigger world of possibilities.",
    }),
  ).toBeVisible();
  await page
    .getByRole("textbox", { name: "Search signals" })
    .fill("no-match-for-this-phrase");
  await expect(
    page.getByRole("heading", { name: "No signals found." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear search" }).click();
  await expect(page.locator(".signal-card")).toHaveCount(2);
});

test("publishing creates a private clone for a visitor and unpublishing revokes the page and image", async ({
  page,
  browser,
  request,
}) => {
  const ownerToken = await openWorkspace(page);
  const publicName = 'E2E "public" & <watchlist>';
  const card = await createMonitor(page, publicName);
  await card.getByRole("button", { name: "Share", exact: true }).click();
  await page
    .getByRole("button", { name: "Publish watchlist", exact: true })
    .click();
  await expect(
    page.getByRole("textbox", { name: "Public watchlist link" }),
  ).toBeVisible();
  const publicLink = await page
    .getByRole("textbox", { name: "Public watchlist link" })
    .inputValue();
  const path = new URL(publicLink).pathname;
  const slug = path.split("/").at(-1)!;

  const publicResponse = await request.get(`/api/public/${slug}`);
  expect(publicResponse.ok()).toBeTruthy();
  const publicBody = await publicResponse.json();
  expect(publicBody.monitor).not.toHaveProperty("workspace_id");
  expect(publicBody.monitor).not.toHaveProperty("webhook_url");
  expect(JSON.stringify(publicBody)).not.toContain(ownerToken);

  const visitor = await browser.newContext({
    baseURL: new URL(page.url()).origin,
  });
  const visitorPage = await visitor.newPage();
  try {
    await visitorPage.goto(publicLink);
    await expect(
      visitorPage.getByRole("heading", { name: publicName, exact: true }),
    ).toBeVisible();
    await expect(
      visitorPage.locator('meta[property="og:title"]'),
    ).toHaveAttribute("content", `${publicName} | A Subabot watchlist`);
    const imageUrl = await visitorPage
      .locator('meta[property="og:image"]')
      .getAttribute("content");
    expect(imageUrl).toContain(`${path}/og.png`);
    const preview = await request.get(`${path}/og.png`);
    expect(preview.ok()).toBeTruthy();
    expect(preview.headers()["content-type"]).toBe("image/png");
    const image = await preview.body();
    expect(
      image
        .subarray(0, 8)
        .equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])),
    ).toBe(true);
    expect(image.readUInt32BE(16)).toBe(1200);
    expect(image.readUInt32BE(20)).toBe(630);

    await visitorPage
      .getByRole("link", { name: "Make this watchlist yours" })
      .click();
    const cloneDialog = visitorPage.getByRole("dialog");
    await expect(cloneDialog).toBeVisible();
    await expect(
      cloneDialog.getByRole("textbox", { name: "Monitor name", exact: true }),
    ).toHaveValue(publicName);
    const visitorToken = await visitorPage.evaluate(
      (key) => localStorage.getItem(key),
      TOKEN_KEY,
    );
    expect(visitorToken).toBeTruthy();
    createdTokens.add(visitorToken!);
    await cloneDialog
      .getByRole("button", { name: "Create monitor", exact: true })
      .click();
    await expect(cloneDialog).toBeHidden();
    const cloned = await monitors(request, visitorToken!);
    const original = await monitors(request, ownerToken);
    expect(cloned).toHaveLength(1);
    expect(cloned[0].id).not.toBe(original[0].id);
    expect(cloned[0].public).toBe(false);
    expect(cloned[0].share_slug).toBeNull();
    expect(cloned[0].feed_urls).toEqual(original[0].feed_urls);
    const forbidden = await request.patch(`/api/monitors/${original[0].id}`, {
      headers: authorization(visitorToken!),
      data: { name: "Should not work" },
    });
    expect(forbidden.status()).toBe(404);

    await page.getByRole("button", { name: "Unpublish", exact: true }).click();
    await expect(
      page.getByRole("button", { name: "Publish watchlist", exact: true }),
    ).toBeVisible();
    const withdrawn = await visitorPage.goto(publicLink);
    expect(withdrawn?.status()).toBe(404);
    await expect(
      visitorPage.getByRole("heading", {
        name: "This watchlist isn’t available.",
      }),
    ).toBeVisible();
    await expect(visitorPage.locator('meta[name="robots"]')).toHaveAttribute(
      "content",
      "noindex,nofollow",
    );
    expect((await request.get(`${path}/og.png`)).status()).toBe(404);
  } finally {
    await visitor.close();
  }
});

test("workspace settings export a recovery key that restores the same private workspace", async ({
  page,
  browser,
  request,
}) => {
  const token = await openWorkspace(page);
  await page
    .getByRole("button", { name: "Workspace settings", exact: true })
    .click();
  const settings = page.getByRole("dialog");
  await settings
    .getByRole("textbox", { name: "Workspace name" })
    .fill("E2E recovered workspace");
  await settings.getByRole("button", { name: "Save", exact: true }).click();
  await expect(page.locator(".workspace-switch strong")).toHaveText(
    "E2E recovered workspace",
  );
  const downloadEvent = page.waitForEvent("download");
  await settings
    .getByRole("button", { name: "Save recovery key", exact: true })
    .click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toBe("subabot-private-recovery.json");
  const downloaded = JSON.parse(
    await readFile((await download.path())!, "utf8"),
  );
  expect(downloaded.token).toBe(token);

  const otherContext = await browser.newContext({
    baseURL: new URL(page.url()).origin,
  });
  const otherPage = await otherContext.newPage();
  try {
    const temporaryToken = await openWorkspace(otherPage);
    await otherPage
      .getByRole("button", { name: "Workspace settings", exact: true })
      .click();
    await otherPage
      .getByRole("button", { name: "Restore a workspace", exact: true })
      .click();
    await otherPage
      .getByRole("textbox", { name: /^Private recovery key/ })
      .fill("invalid-key");
    await otherPage
      .getByRole("button", { name: "Restore workspace", exact: true })
      .click();
    await expect(otherPage.getByRole("alert")).toContainText(
      "could not be verified",
    );
    expect(
      await otherPage.evaluate((key) => localStorage.getItem(key), TOKEN_KEY),
    ).toBe(temporaryToken);
    await otherPage
      .getByRole("textbox", { name: /^Private recovery key/ })
      .fill(JSON.stringify(downloaded));
    await otherPage
      .getByRole("button", { name: "Restore workspace", exact: true })
      .click();
    await expect(otherPage.getByRole("dialog")).toBeHidden();
    await expect(otherPage.locator(".workspace-switch strong")).toHaveText(
      "E2E recovered workspace",
    );
    expect(
      await otherPage.evaluate((key) => localStorage.getItem(key), TOKEN_KEY),
    ).toBe(token);
    const workspace = await request.get("/api/workspace", {
      headers: authorization(token),
    });
    expect((await workspace.json()).workspace.name).toBe(
      "E2E recovered workspace",
    );
  } finally {
    await otherContext.close();
  }
});

test("the template gallery filters and stays usable on a narrow viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/explore");
  await expect(
    page.getByRole("heading", { name: /rabbit hole/ }),
  ).toBeVisible();
  await page
    .getByRole("searchbox", { name: "Search watchlists" })
    .fill("AI radar");
  await expect(page.locator("[data-template-card]:visible")).toHaveCount(1);
  await expect(
    page.getByRole("heading", { name: "AI radar", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("searchbox", { name: "Search watchlists" })
    .fill("impossible-template-name");
  await expect(
    page.getByRole("heading", { name: "No watchlists found." }),
  ).toBeVisible();
  await page.getByRole("searchbox", { name: "Search watchlists" }).fill("");
  await page.getByRole("button", { name: "Design", exact: true }).click();
  await expect(page.locator("[data-template-card]:visible")).toHaveCount(1);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
