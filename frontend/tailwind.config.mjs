import typography from "@tailwindcss/typography";
import daisyui from "daisyui";
import colors from "tailwindcss/colors";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: {
    extend: {},
  },
  plugins: [typography, daisyui],
  daisyui: {
    themes: [
      {
        subabot: {
          primary: "#203a43",
          secondary: "#2c5364",
          accent: "#b0c4de",
          neutral: "#0f2027",
          "base-100": colors.slate[300],
          info: "#3abff8",
          success: "#36d399",
          warning: "#fbbd23",
          error: "#f87272",
        },
      },
    ],
  },
};
