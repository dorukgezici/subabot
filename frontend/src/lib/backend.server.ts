// Import only from server-rendered pages and endpoints. Never from React islands.
export function backendHeaders(): Record<string, string> {
  const secret = process.env.BACKEND_PROXY_SECRET;
  return secret ? { "x-subabot-proxy-secret": secret } : {};
}
