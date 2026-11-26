/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Light & Dark theme tokens
        background: "var(--background)",
        card: "var(--card)",
        primary: "var(--primary)",
        "text-primary": "var(--text-primary)",
        "text-secondary": "var(--text-secondary)",
        border: "var(--border)",

        // Semantic Colors
        buy: "#10B981",
        sell: "#EF4444",
        hold: "#F59E0B",
        neutral: "#64748B",
      },
      borderRadius: {
        card: "14px",
      },
    },
  },
  plugins: [],
}
