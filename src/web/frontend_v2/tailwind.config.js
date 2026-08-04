/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'cyber-black': '#050a14',
        'cyber-dark': '#0a192f',
        'cyber-blue': '#00f3ff',
        'cyber-cyan': '#0afff0',
        'cyber-pink': '#ff00ff',
        'alert-red': '#ff2a2a',
        'safe-green': '#00ff41',
      },
      fontFamily: {
        'mono': ['"Share Tech Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        'sans': ['"Orbitron"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
      }
    },
  },
  plugins: [],
}
