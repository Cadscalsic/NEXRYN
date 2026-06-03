import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        graphite: {
          950: "#07090d",
          900: "#0c1017",
          850: "#111722",
          800: "#151c28",
        },
        nexryn: {
          cyan: "#35d7ff",
          blue: "#3b82f6",
          violet: "#8b5cf6",
          mint: "#56f0bd",
          amber: "#f4c95d",
        },
      },
      boxShadow: {
        "runtime": "0 20px 60px rgba(0, 0, 0, 0.34)",
        "cyan-soft": "0 0 28px rgba(53, 215, 255, 0.16)",
      },
    },
  },
  plugins: [],
} satisfies Config;
