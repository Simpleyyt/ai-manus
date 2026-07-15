/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        // 与 manus.im 官方一致:font-serif 优先 Libre Baskerville
        serif: ['"Libre Baskerville"', 'LibreBaskerville', 'Georgia', 'Cambria', 'ui-serif', '"Times New Roman"', 'Times', 'serif'],
      },
    },
  },
  darkMode: 'class',
  plugins: [
    require('@tailwindcss/typography'),
  ],
} 