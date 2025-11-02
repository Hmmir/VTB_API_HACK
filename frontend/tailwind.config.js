const withOpacityValue = (variable) => ({ opacityValue }) => {
  if (opacityValue === undefined) {
    return `rgb(var(${variable}))`;
  }

  return `rgb(var(${variable}) / ${opacityValue})`;
};

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Unbounded"', '"Bricolage Grotesque"', 'sans-serif'],
        body: ['"Bricolage Grotesque"', 'sans-serif'],
        mono: ['"Azeret Mono"', 'monospace'],
      },
      colors: {
        primary: {
          50: withOpacityValue('--palette-primary-50'),
          100: withOpacityValue('--palette-primary-100'),
          200: withOpacityValue('--palette-primary-200'),
          300: withOpacityValue('--palette-primary-300'),
          400: withOpacityValue('--palette-primary-400'),
          500: withOpacityValue('--palette-primary-500'),
          600: withOpacityValue('--palette-primary-600'),
          700: withOpacityValue('--palette-primary-700'),
          800: withOpacityValue('--palette-primary-800'),
          900: withOpacityValue('--palette-primary-900'),
        },
        ink: withOpacityValue('--palette-ink'),
        sand: withOpacityValue('--palette-sand'),
        dusk: withOpacityValue('--palette-dusk'),
        glow: withOpacityValue('--palette-glow'),
        roseflare: withOpacityValue('--palette-roseflare'),
      },
      backgroundImage: {
        "orb-web": "radial-gradient(120% 120% at 0% 0%, rgba(32, 86, 105, 0.28), transparent 60%), radial-gradient(80% 80% at 100% 0%, rgba(255, 111, 145, 0.2), transparent 70%)",
        "noise-soft": "linear-gradient(135deg, rgba(240, 244, 255, 0.92) 0%, rgba(252, 246, 240, 0.85) 100%)",
      },
      boxShadow: {
        prism: '0 20px 45px rgba(18, 35, 52, 0.22)',
        bevel: 'inset 0 1px 0 rgba(255,255,255,0.4), 0 1px 0 rgba(9,13,21,0.18)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(18px) scale(0.98)' },
          '100%': { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        'dash-glow': {
          '0%, 100%': { opacity: '0.55' },
          '50%': { opacity: '0.92' },
        },
        'float-slow': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.65s cubic-bezier(0.19, 1, 0.22, 1)',
        'dash-glow': 'dash-glow 3.4s ease-in-out infinite',
        'float-slow': 'float-slow 8s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}

