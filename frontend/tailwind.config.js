/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'cyber-black': '#0A0A0F',
        'cyber-dark': '#12121A',
        'cyber-card': '#1A1A2E',
        'neon-cyan': '#00F3FF',
        'neon-purple': '#BC13FE',
        'acid-yellow': '#FCEE0A',
        'cyber-border': '#2A2A3E',
      },
      fontFamily: {
        'display': ['Orbitron', 'Rajdhani', 'sans-serif'],
        'body': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['Geist Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'neon-cyan': '0 0 15px rgba(0, 243, 255, 0.3)',
        'neon-cyan-lg': '0 0 30px rgba(0, 243, 255, 0.5)',
        'neon-purple': '0 0 15px rgba(188, 19, 254, 0.3)',
        'card-hover': '0 0 20px rgba(0, 243, 255, 0.2), 0 4px 20px rgba(0, 0, 0, 0.4)',
      },
      animation: {
        'glitch': 'glitch 0.3s cubic-bezier(0.36, 0.07, 0.19, 0.97) both',
        'neon-pulse': 'neon-pulse 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'scanline': 'scanline 8s linear infinite',
      },
      keyframes: {
        glitch: {
          '0%': { transform: 'translate(0)' },
          '20%': { transform: 'translate(-2px, 2px)' },
          '40%': { transform: 'translate(-2px, -2px)' },
          '60%': { transform: 'translate(2px, 2px)' },
          '80%': { transform: 'translate(2px, -2px)' },
          '100%': { transform: 'translate(0)' },
        },
        'neon-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)"' },
        },
      },
      clipPath: {
        'cyber-corner': 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))',
        'cyber-btn': 'polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px)',
      },
    },
  },
  plugins: [],
};
