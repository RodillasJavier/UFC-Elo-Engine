/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'ufc-black':   '#0A0A0A',
        'ufc-white':   '#F5F5F0',
        'ufc-red':     '#E10600',
        'ufc-gray':    '#333333',
        'ufc-darkgray':'#1A1A1A',
      },
      fontFamily: {
        display: ['Anton', 'Impact', 'sans-serif'],
        body:    ['Inter', '"Helvetica Neue"', 'sans-serif'],
        mono:    ['"JetBrains Mono"', '"Courier New"', 'monospace'],
      },
    },
  },
  plugins: [],
}
