/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0a1628',
          800: '#0f2040',
          700: '#132952',
        },
        cyan: { DEFAULT: '#06b6d4' },
        seafoam: { DEFAULT: '#34d399' },
      }
    }
  },
  plugins: [],
}