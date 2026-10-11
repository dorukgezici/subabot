export interface Workspace {
  id: string;
  name: string;
  created_at?: string;
}
export interface Monitor {
  id: string;
  name: string;
  description: string;
  keywords: string[];
  exclude_keywords: string[];
  match_mode: "any" | "all";
  feed_urls: string[];
  enabled: boolean;
  color: string;
  public: boolean;
  share_slug: string | null;
  created_at: string;
  last_checked_at: string | null;
  last_error?: string | null;
}
export interface Signal {
  id: string;
  monitor_id: string;
  title: string;
  url: string;
  summary: string;
  source: string;
  published_at: string | null;
  matched_keywords: string[];
  is_read: boolean;
  is_bookmarked: boolean;
}
export interface Template {
  id: string;
  name: string;
  description: string;
  keywords: string[];
  feed_urls: string[];
  color: string;
  category: string;
}
export interface WorkspaceResponse {
  workspace: Workspace;
  slack: { connected: boolean };
  stats: {
    monitors: number;
    signals: number;
    unread: number;
    bookmarked?: number;
  };
}
export interface PublicMonitor {
  monitor: Pick<
    Monitor,
    | "name"
    | "description"
    | "keywords"
    | "exclude_keywords"
    | "match_mode"
    | "feed_urls"
    | "color"
    | "share_slug"
  >;
  signals: Signal[];
}
export const TOKEN_KEY = "subabot.workspace.v1";
export function token() {
  return localStorage.getItem(TOKEN_KEY);
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const key = token();
  if (key) headers.set("Authorization", `Bearer ${key}`);
  const response = await fetch(`/api${path}`, {
    ...options,
    headers,
    signal:
      options.signal ||
      AbortSignal.timeout(path === "/scan" ? 125_000 : 20_000),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = Array.isArray(body.detail)
      ? body.detail.map((x: { msg: string }) => x.msg).join(". ")
      : body.detail;
    throw new Error(
      message || `Request failed (${response.status}). Please try again.`,
    );
  }
  return response.status === 204 ? (undefined as T) : await response.json();
}
let creating: Promise<void> | null = null;
export async function ensureWorkspace() {
  if (token()) return;
  if (!creating)
    creating = api<{ token: string }>("/workspaces", {
      method: "POST",
      body: JSON.stringify({ name: "My workspace" }),
    })
      .then((data) => {
        localStorage.setItem(TOKEN_KEY, data.token);
      })
      .finally(() => {
        creating = null;
      });
  await creating;
}
export const json = (method: string, body?: unknown): RequestInit => ({
  method,
  ...(body === undefined ? {} : { body: JSON.stringify(body) }),
});
export function safeLink(value: string) {
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "#";
  } catch {
    return "#";
  }
}
export function timeAgo(value: string | null) {
  if (!value) return "Recently";
  const diff = Math.max(0, Date.now() - new Date(value).getTime());
  if (!Number.isFinite(diff)) return "Recently";
  const hours = Math.floor(diff / 3600000);
  return hours < 1
    ? "Just now"
    : hours < 24
      ? `${hours}h ago`
      : `${Math.floor(hours / 24)}d ago`;
}
