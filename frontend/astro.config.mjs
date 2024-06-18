import react from "@astrojs/react";
import svelte from "@astrojs/svelte";
import tailwind from "@astrojs/tailwind";
import vercel from "@astrojs/vercel/serverless";
import { defineConfig } from "astro/config";

// https://astro.build/config
export default defineConfig({
  output: "hybrid",
  experimental: {
    actions: true,
  },
  integrations: [tailwind(), react(), svelte()],
  adapter: vercel(),
});
