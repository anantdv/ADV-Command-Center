/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#101828',
        muted: '#667085',
        surface: '#f6f7fb',
        brand: { 50: '#eef2ff', 500: '#6366f1', 600: '#5547e8', 700: '#4338ca' }
      },
      boxShadow: { card: '0 1px 2px rgba(16,24,40,.04), 0 8px 24px rgba(16,24,40,.04)' },
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] }
    }
  },
  plugins: []
}
