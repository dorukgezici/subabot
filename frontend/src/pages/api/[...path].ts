import type { APIRoute } from "astro";
import { backendHeaders } from "@/lib/backend.server";
export const prerender = false;
const forward: APIRoute = async ({ request, params, url, clientAddress }) => {
  const path = params.path || "";
  if (!/^[a-zA-Z0-9_\-/]+$/.test(path) || path.includes(".."))
    return new Response("Not found", { status: 404 });
  const target = new URL(
    `/api/${path}${url.search}`,
    process.env.BACKEND_URL ||
      import.meta.env.BACKEND_URL ||
      "http://127.0.0.1:8000",
  );
  const headers = new Headers({
    ...backendHeaders(),
    Accept: "application/json",
    "x-subabot-client-address": clientAddress,
  });
  for (const name of ["authorization", "content-type"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  try {
    const maxBytes = 32_768;
    const tooLarge = () =>
      Response.json({ detail: "Request is too large." }, { status: 413 });
    if (Number(request.headers.get("content-length")) > maxBytes)
      return tooLarge();
    let body: Uint8Array | undefined;
    if (!["GET", "HEAD"].includes(request.method) && request.body) {
      const reader = request.body.getReader();
      const chunks: Uint8Array[] = [];
      let size = 0;
      while (true) {
        const part = await reader.read();
        if (part.done) break;
        size += part.value.byteLength;
        if (size > maxBytes) {
          await reader.cancel();
          return tooLarge();
        }
        chunks.push(part.value);
      }
      body = new Uint8Array(size);
      let offset = 0;
      for (const chunk of chunks) {
        body.set(chunk, offset);
        offset += chunk.length;
      }
    }
    const response = await fetch(target, {
      method: request.method,
      headers,
      body: body as BodyInit | undefined,
      redirect: "error",
      signal: AbortSignal.timeout(path === "scan" ? 130_000 : 15_000),
    });
    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type":
          response.headers.get("content-type") || "application/json",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch {
    return Response.json(
      {
        detail:
          "The signal service is unavailable. Please try again in a moment.",
      },
      { status: 503 },
    );
  }
};
export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const DELETE = forward;
