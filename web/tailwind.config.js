/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    screens: {
      'xs': '375px',
      'sm': '640px',
      'md': '768px',
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1536px',
    },
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
          DEFAULT: 'rgb(var(--color-primary-500) / <alpha-value>)',
          50: 'rgb(var(--color-primary-500) / 0.1)',
          100: 'rgb(var(--color-primary-500) / 0.2)',
          200: 'rgb(var(--color-primary-500) / 0.3)',
          300: 'rgb(var(--color-primary-500) / 0.5)',
          400: 'rgb(var(--color-primary-500) / 0.7)',
          500: 'rgb(var(--color-primary-500) / <alpha-value>)',
          600: 'rgb(var(--color-primary-500) / 0.85)',
          700: 'rgb(var(--color-primary-500) / 0.7)',
          800: 'rgb(var(--color-primary-500) / 0.6)',
          900: 'rgb(var(--color-primary-500) / 0.5)',
        },
        brand: {
          strong: 'rgb(var(--color-brand-strong) / <alpha-value>)',
          surface: 'rgb(var(--color-brand-surface) / <alpha-value>)',
          border: 'rgb(var(--color-brand-border) / <alpha-value>)',
          contrast: 'rgb(var(--color-brand-contrast) / <alpha-value>)',
        },
        accent: {
          earth: 'rgb(var(--color-accent-earth) / <alpha-value>)',
          rose: 'rgb(var(--color-accent-rose) / <alpha-value>)',
          teal: 'rgb(var(--color-accent-teal) / <alpha-value>)',
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
        'primary-gradient': 'linear-gradient(135deg, rgb(var(--color-brand-strong)) 0%, rgb(var(--color-primary-500)) 100%)',
        'surface-gradient': 'linear-gradient(180deg, rgb(var(--color-surface-50) / 0.98) 0%, rgb(var(--color-surface-100) / 0.98) 100%)',
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 12px 28px -24px rgb(var(--shadow-soft) / 0.14)',
        'glass': '0 16px 32px -24px rgb(var(--shadow-glass) / 0.14)',
        'glow': '0 8px 18px rgb(var(--shadow-soft) / 0.1)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
      },
    },
  },
  plugins: [],
  corePlugins: {
    preflight: true,
  },
}
