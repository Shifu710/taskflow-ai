import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        panel: "#111827",
        line: "#d9dee8",
        accent: "#0f766e",
        gold: "#b7791f"
      }
    }
  },
  plugins: []
};

export default config;
