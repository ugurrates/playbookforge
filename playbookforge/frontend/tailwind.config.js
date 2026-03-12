/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        tactical: {
          bg: {
            primary: "#0a0f0a",
            secondary: "#111a11",
            card: "#0f1a0f",
            sidebar: "#080d08",
          },
          border: {
            DEFAULT: "#1a2e1a",
            highlight: "#2a3e2a",
          },
          text: {
            primary: "#d4d4c8",
            secondary: "#7a7a6a",
          },
          accent: {
            DEFAULT: "#f59e0b",
            hover: "#d97706",
            muted: "rgba(245, 158, 11, 0.2)",
          },
          success: "#22c55e",
          error: "#ef4444",
          warning: "#f59e0b",
          info: "#06b6d4",
        },
      },
      fontFamily: {
        mono: [
          "'JetBrains Mono'",
          "'Fira Code'",
          "'Cascadia Code'",
          "ui-monospace",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};
