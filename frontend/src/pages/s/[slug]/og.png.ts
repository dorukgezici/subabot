import type { APIRoute } from "astro";
import { backendHeaders } from "@/lib/backend.server";
import { Resvg } from "@resvg/resvg-js";
import { resolve } from "node:path";

// Included in both deployment bundles so rendering never depends on host OS fonts.
const previewFont = resolve(process.cwd(), "assets/fonts/DMSans.ttf");

const escapeXml = (text: string) =>
  text.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, "").replace(
    /[&<>"']/g,
    (char) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&apos;",
      })[char]!,
  );

function lines(text: string, length: number, maximum: number) {
  const words = text.replace(/\s+/g, " ").trim().split(" ");
  const result: string[] = [];
  let line = "";
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (next.length > length && line) {
      result.push(line);
      line = word;
    } else line = next;
  }
  if (line) result.push(line);
  return result.slice(0, maximum).map((value, index) => {
    const clipped =
      value.length > length ? `${value.slice(0, length - 1)}…` : value;
    return index === maximum - 1 && result.length > maximum
      ? `${clipped.slice(0, length - 1)}…`
      : clipped;
  });
}

function reportPreviewFailure(stage: "fetch" | "render", error: unknown) {
  const cause = error instanceof Error ? error.cause : undefined;
  const networkCode =
    cause && typeof cause === "object" && "code" in cause
      ? String(cause.code)
      : undefined;
  // Log failure stages, never watchlist content, capability tokens, or request headers.
  console.warn("[subabot:public-preview]", {
    stage,
    errorType: error instanceof Error ? error.name : "UnknownError",
    networkCode,
  });
}

export const GET: APIRoute = async ({ params }) => {
  let payload: {
    monitor: {
      name: string;
      description: string;
      keywords: string[];
      color: string;
      feed_urls?: string[];
    };
  };
  try {
    const response = await fetch(
      `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/api/public/${encodeURIComponent(params.slug || "")}`,
      { headers: backendHeaders(), signal: AbortSignal.timeout(8000) },
    );
    if (response.status === 404)
      return new Response("Watchlist not found", {
        status: 404,
        headers: { "Cache-Control": "no-store" },
      });
    if (!response.ok)
      throw new Error("Unavailable", {
        cause: { code: `HTTP_${response.status}` },
      });
    payload = await response.json();
  } catch (error) {
    reportPreviewFailure("fetch", error);
    return new Response("Watchlist temporarily unavailable", {
      status: 503,
      headers: { "Cache-Control": "no-store", "Retry-After": "30" },
    });
  }
  const monitor = payload.monitor;
  const accent = /^#[\da-f]{6}$/i.test(monitor.color)
    ? monitor.color
    : "#357a57";
  const title = lines(monitor.name, 29, 2);
  const subtitle = lines(
    monitor.description || "Interesting things. Found for you.",
    54,
    2,
  );
  let keywordX = 64;
  const keywords = monitor.keywords
    .slice(0, 4)
    .map((keyword) => {
      const text = keyword.length > 18 ? `${keyword.slice(0, 17)}…` : keyword;
      const width = text.length * 9 + 28;
      const item = `<rect x="${keywordX}" y="449" width="${width}" height="35" rx="7" fill="#e9f0e3"/><text x="${keywordX + 14}" y="472" font-size="15" fill="#5e7952">${escapeXml(text)}</text>`;
      keywordX += width + 9;
      return item;
    })
    .join("");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
    <rect width="1200" height="630" fill="#f7f8f3"/>
    <circle cx="1050" cy="280" r="245" fill="#eef3e9"/>
    <circle cx="1050" cy="280" r="181" fill="none" stroke="#dce6d4" stroke-width="2"/>
    <circle cx="1050" cy="280" r="112" fill="none" stroke="#d3e0c9" stroke-width="2" stroke-dasharray="5 8"/>
    <circle cx="1050" cy="280" r="65" fill="${accent}" opacity=".12"/>
    <g transform="translate(1025,255)" fill="none" stroke="${accent}" stroke-width="5" stroke-linecap="round"><path d="M4 19a27 27 0 0 1 27 27"/><path d="M4 4a42 42 0 0 1 42 42"/><circle cx="6" cy="44" r="3" fill="${accent}" stroke="none"/></g>
    <circle cx="967" cy="119" r="7" fill="#7e9d6c"/>
    <circle cx="1147" cy="404" r="7" fill="#91ab82"/>
    <g font-family="DM Sans, sans-serif">
      <rect x="64" y="54" width="35" height="35" rx="10" fill="#d8e8cd"/>
      <g transform="translate(73,64)" fill="none" stroke="#4e7540" stroke-width="2.2" stroke-linecap="round"><path d="M0 5a10 10 0 0 1 10 10"/><path d="M0 0a15 15 0 0 1 15 15"/><circle cx="1" cy="15" r="1.5" fill="#4e7540" stroke="none"/></g>
      <text x="111" y="81" font-size="27" font-weight="700" fill="#26371f">subabot</text>
      <text x="64" y="163" font-size="12" letter-spacing="3" fill="#7b926b">A PUBLIC WATCHLIST</text>
      ${title.map((text, index) => `<text x="60" y="${245 + index * 66}" font-size="56" font-weight="700" fill="#253420">${escapeXml(text)}</text>`).join("")}
      ${subtitle.map((text, index) => `<text x="64" y="${362 + index * 28}" font-size="20" fill="#8a987f">${escapeXml(text)}</text>`).join("")}
      ${keywords}
      <line x1="64" y1="529" x2="1136" y2="529" stroke="#dde5d5"/>
      <text x="64" y="576" font-size="17" fill="#6b855b">Make this watchlist yours ↗</text>
      <text x="1136" y="576" text-anchor="end" font-size="14" fill="#8b9b7f">Built by Doruk Gezici</text>
    </g>
  </svg>`;
  try {
    const png = new Resvg(svg, {
      font: {
        loadSystemFonts: false,
        fontFiles: [previewFont],
        defaultFontFamily: "DM Sans",
      },
    })
      .render()
      .asPng();
    return new Response(new Uint8Array(png), {
      headers: {
        "Content-Type": "image/png",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch (error) {
    reportPreviewFailure("render", error);
    return new Response("Preview temporarily unavailable", {
      status: 503,
      headers: { "Cache-Control": "no-store", "Retry-After": "30" },
    });
  }
};
