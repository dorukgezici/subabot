import type { APIRoute } from "astro";

export const GET: APIRoute = ({ url }) => {
  const origin = new URL(
    process.env.PUBLIC_SITE_URL ||
      import.meta.env.PUBLIC_SITE_URL ||
      url.origin,
  ).origin;
  return new Response(
    `User-agent: *\nAllow: /\nDisallow: /dashboard\nDisallow: /api/\n\nSitemap: ${origin}/sitemap.xml\n`,
    {
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    },
  );
};
