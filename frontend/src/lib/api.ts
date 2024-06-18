type Fetch = typeof fetch;

// feeds
export async function getFeeds(fetch: Fetch): Promise<Feed[]> {
  const res = await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/feeds`, {
    cache: "no-store",
  });
  if (!res.ok) return [];
  return await res.json();
}

export async function createFeed(fetch: Fetch, url: string): Promise<Feed> {
  const res = await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/feeds`, {
    method: "POST",
    body: JSON.stringify({ key: url }),
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to create feed!");
  return await res.json();
}

export async function deleteFeed(fetch: Fetch, url: string): Promise<void> {
  await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/feeds`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key: url }),
  });
}

export async function importFeeds(fetch: Fetch): Promise<Feed[]> {
  const res = await fetch(
    `${import.meta.env.PUBLIC_BACKEND_URL}/feeds/import`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error("Failed to import feeds!");
  return await res.json();
}

// keywords
export async function getKeywords(fetch: Fetch): Promise<Keyword[]> {
  const res = await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/keywords`, {
    cache: "no-store",
  });
  if (!res.ok) return [];
  return await res.json();
}

export async function createKeyword(
  fetch: Fetch,
  value: string,
): Promise<Keyword> {
  const res = await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/keywords`, {
    method: "POST",
    body: JSON.stringify({ value }),
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to create keyword!");
  return await res.json();
}

export async function deleteKeyword(fetch: Fetch, key: string): Promise<void> {
  await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/keywords/${key}`, {
    method: "DELETE",
  });
}

// crawler
export async function triggerCrawl(fetch: Fetch): Promise<void> {
  await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/__space/v0/actions`, {
    method: "POST",
    body: JSON.stringify({ event: { id: "trigger_crawl", trigger: "manuel" } }),
    headers: { "Content-Type": "application/json" },
  });
}
