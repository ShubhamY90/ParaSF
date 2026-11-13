/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: "#0f1729", 800: "#1a2744", 700: "#243356", 600: "#2e4068" },
        brand: { green: "#22c55e", blue: "#3b82f6" },
      },
    },
  },
  plugins: [],
};
