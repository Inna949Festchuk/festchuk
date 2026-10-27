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
        'cyber-black': '#060812',
        'cyber-dark': '#0D1021',
        'cyber-card': '#12172E',
        'neon-cyan': '#00F3FF',
        'neon-purple': '#BC13FE',
        'neon-magenta': '#FF2BD6',
        'acid-yellow': '#FCEE0A',
        'cyber-border': '#232F4E',
      },
      fontFamily: {
        'display': ['Orbitron', 'Unbounded', 'Rajdhani', 'sans-serif'],
        'body': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'neon-cyan': '0 0 18px rgba(0, 243, 255, 0.35)',
        'neon-cyan-lg': '0 0 34px rgba(0, 243, 255, 0.55)',
        'neon-purple': '0 0 18px rgba(188, 19, 254, 0.35)',
        'neon-magenta': '0 0 22px rgba(255, 43, 214, 0.45)',
        'card-hover': '0 0 25px rgba(0, 243, 255, 0.22), 0 8px 30px rgba(0, 0, 0, 0.55)',
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
          '50%': { opacity: '0.65' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
      clipPath: {
        'cyber-corner': 'polygon(0 0, calc(100% - 14px) 0, 100% 14px, 100% 100%, 14px 100%, 0 calc(100% - 14px))',
        'cyber-btn': 'polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)',
      },
    },
  },
  plugins: [],
};
