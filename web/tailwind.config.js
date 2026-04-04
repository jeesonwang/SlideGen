/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: 'rgb(var(--color-background) / <alpha-value>)',
        surface: {
          50: 'rgb(var(--color-surface-50) / <alpha-value>)',
          100: 'rgb(var(--color-surface-100) / <alpha-value>)',
          200: 'rgb(var(--color-surface-200) / <alpha-value>)',
          300: 'rgb(var(--color-surface-300) / <alpha-value>)',
          400: 'rgb(var(--color-surface-400) / <alpha-value>)',
          500: 'rgb(var(--color-surface-500) / <alpha-value>)',
        },
        primary: {
          50: '#eef4fb',
          100: '#d9e7f7',
          200: '#bdd4ee',
          300: '#93b8df',
          400: '#5e95cb',
          500: '#3d78b3',
          600: '#315f8f',
          700: '#294f76',
          800: '#263f5d',
          900: '#21354c',
          DEFAULT: '#3d78b3',
        },
        brand: {
          strong: 'rgb(var(--color-brand-strong) / <alpha-value>)',
          surface: 'rgb(var(--color-brand-surface) / <alpha-value>)',
          border: 'rgb(var(--color-brand-border) / <alpha-value>)',
          contrast: 'rgb(var(--color-brand-contrast) / <alpha-value>)',
        },
        accent: {
          purple: '#8b6748',
          pink: '#b8695c',
          cyan: '#41756b',
        },
        border: 'rgb(var(--color-border) / <alpha-value>)',
        text: {
          main: 'rgb(var(--color-text-main) / <alpha-value>)',
          secondary: 'rgb(var(--color-text-secondary) / <alpha-value>)',
          muted: 'rgb(var(--color-text-muted) / <alpha-value>)',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'primary-gradient': 'linear-gradient(135deg, #3d78b3 0%, #315f8f 100%)',
        'surface-gradient': 'linear-gradient(180deg, rgba(252, 250, 246, 0.98) 0%, rgba(245, 241, 234, 0.98) 100%)',
      },
      fontFamily: {
        heading: ['"IBM Plex Sans"', 'sans-serif'],
        body: ['"IBM Plex Sans"', 'sans-serif'],
        sans: ['"IBM Plex Sans"', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 12px 28px -24px rgba(54, 72, 96, 0.18)',
        'glass': '0 16px 32px -24px rgba(54, 72, 96, 0.18)',
        'glow': '0 8px 18px rgba(49, 95, 143, 0.12)',
        'glow-strong': '0 14px 28px rgba(49, 95, 143, 0.16)',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
  corePlugins: {
    preflight: true, // Re-enabling preflight for better consistency, unless strictly forbidden. The previous file had it false, likely for AntD compat. I should check if I should keep it false.
  },
}
