/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'ufc-red': '#CC0A0A',
        'ufc-gold': '#C49A14',
      },
      fontFamily: {
        display: ['"Barlow Condensed"', 'Impact', 'sans-serif'],
        body: ['Barlow', '"Helvetica Neue"', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Courier New"', 'monospace'],
      },
    },
  },
  plugins: [],
}
