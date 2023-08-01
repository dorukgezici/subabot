/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "var(--primary)",
        dark: "var(--dark)",
        light: "var(--light)",
        lighter: "var(--lighter)",
      },
    },
  },
  plugins: [require("daisyui")],
};
