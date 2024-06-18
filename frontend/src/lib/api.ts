import type { Feed, Keyword } from "@/types/rss";

// feeds
export async function getFeeds(): Promise<Feed[]> {
  const res = await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/feeds`, {
    cache: "no-store",
  });
  if (!res.ok) return [];
  return await res.json();
}

export async function createFeed(url: string): Promise<Feed> {
  const res = await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/feeds`, {
    method: "POST",
    body: JSON.stringify({ key: url }),
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to create feed!");
  return await res.json();
}

export async function deleteFeed(url: string): Promise<void> {
  await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/feeds`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key: url }),
  });
}

export async function importFeeds(): Promise<Feed[]> {
  const res = await fetch(
    `${import.meta.env.PUBLIC_BACKEND_URL}/feeds/import`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error("Failed to import feeds!");
  return await res.json();
}

// keywords
export async function getKeywords(): Promise<Keyword[]> {
  const res = await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/keywords`, {
    cache: "no-store",
  });
  if (!res.ok) return [];
  return await res.json();
}

export async function createKeyword(value: string): Promise<Keyword> {
  const res = await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/keywords`, {
    method: "POST",
    body: JSON.stringify({ value }),
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to create keyword!");
  return await res.json();
}

export async function deleteKeyword(key: string): Promise<void> {
  await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/keywords/${key}`, {
    method: "DELETE",
  });
}

// crawler
export async function triggerCrawl(): Promise<void> {
  await fetch(`${import.meta.env.PUBLIC_BACKEND_URL}/__space/v0/actions`, {
    method: "POST",
    body: JSON.stringify({ event: { id: "trigger_crawl", trigger: "manuel" } }),
    headers: { "Content-Type": "application/json" },
  });
}
