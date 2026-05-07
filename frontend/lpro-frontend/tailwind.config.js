/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  darkMode: "media",
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#662483',
          dark: '#4f1b66',
          light: '#f3e8ff',
        }
      }
    },
  },
  plugins: [require("tailwindcss"), require("autoprefixer")],
};
