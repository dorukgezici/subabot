import react from "@astrojs/react";
import node from "@astrojs/node";
import vercel from "@astrojs/vercel";
import { defineConfig } from "astro/config";

const isVercel = process.env.VERCEL === "1";
const site = new URL(
  process.env.PUBLIC_SITE_URL ||
    (isVercel ? "https://subabot.gezici.me" : "http://localhost:4321"),
);
const allowedDomains = [
  {
    hostname: site.hostname,
    protocol: site.protocol.slice(0, -1),
    port: site.port,
  },
];
// Trust only exact deployment hostnames supplied by Vercel, never all vercel.app sites.
if (isVercel) {
  for (const hostname of [
    process.env.VERCEL_URL,
    process.env.VERCEL_BRANCH_URL,
    process.env.VERCEL_PROJECT_PRODUCTION_URL,
  ]) {
    if (hostname && /^[a-z0-9-]+\.vercel\.app$/i.test(hostname)) {
      allowedDomains.push({ hostname, protocol: "https", port: "" });
    }
  }
}

export default defineConfig({
  site: site.href,
  output: "server",
  integrations: [react()],
  adapter: isVercel
    ? vercel({
        maxDuration: 180,
        includeFiles: ["./assets/fonts/DMSans.ttf", "./assets/fonts/OFL.txt"],
        staticHeaders: true,
      })
    : node({ mode: "standalone" }),
  security: { allowedDomains },
  server: { host: true },
});
