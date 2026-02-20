/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        srec: {
          primary: "#14532D",
          primaryHover: "#166534",
          primaryLight: "#22C55E",

          gold: "#D4AF37",
          goldLight: "#FACC15",

          background: "#F8FAF8",
          card: "#FFFFFF",

          textPrimary: "#111827",
          textSecondary: "#6B7280",

          border: "#E5E7EB",

          danger: "#EF4444",
          warning: "#FACC15",
        },
        brand: {
          light: '#6ee7b7', // Soft Emerald 300
          DEFAULT: '#10b981', // Emerald 500 - Professional Green
          dark: '#047857', // Emerald 700
        },
        accent: {
          light: '#fde68a', // Amber 200 - Soft Gold highlight
          DEFAULT: '#d97706', // Amber 600 - Muted Gold
          dark: '#b45309', // Amber 700
        },
        background: '#f4f7f6', // Soft cool off-white for page background
        surface: '#ffffff', // Pure white for cards
        success: '#10b981', // Match brand
        error: '#f43f5e', // Soft Rose
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
        // Semantic Action Colors - Raise/Create
        raise: {
          light: '#fecaca',   // soft red for backgrounds
          DEFAULT: '#f87171', // coral red for actions
          dark: '#dc2626',    // darker red for text
        },
        // Priority Colors (pastel/mild)
        priority: {
          low: '#86efac',      // soft green
          medium: '#fcd34d',   // soft amber/yellow  
          high: '#fdba74',     // soft orange
          critical: '#fca5a5', // muted red
        },
        // Status Colors (pastel/mild)
        status: {
          raised: '#93c5fd',   // soft blue
          opened: '#5eead4',   // soft teal
          reviewed: '#c4b5fd', // soft violet
          closed: '#d1d5db',   // soft gray
        },
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(16, 185, 129, 0.05)',
        'neu-flat': '0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)',
        'neu-hover': '0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01)',
        'neu-pressed': 'inset 2px 2px 5px #e2e4e7, inset -2px -2px 5px #ffffff',
        'neu-light': '0 1px 2px rgba(0, 0, 0, 0.05)',
        // Neuromorphic shadows for premium feel
        'neu-inset': 'inset 3px 3px 6px #d1d5db, inset -3px -3px 6px #ffffff',
        'neu-raised': '6px 6px 12px #d1d5db, -6px -6px 12px #ffffff',
        'neu-soft': '4px 4px 8px #d1d5db, -4px -4px 8px #ffffff',
        // Raise button shadows
        'raise-btn': '0 4px 14px -2px rgba(248, 113, 113, 0.35), 0 2px 4px rgba(248, 113, 113, 0.2)',
        'raise-btn-hover': '0 8px 20px -2px rgba(248, 113, 113, 0.45), 0 4px 8px rgba(248, 113, 113, 0.25)',
        'raise-pressed': 'inset 0 2px 4px rgba(0,0,0,0.15)',
        // Vote button glow
        'vote-glow': '0 0 12px rgba(16, 185, 129, 0.4)',
        'vote-glow-down': '0 0 12px rgba(244, 63, 94, 0.4)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
};

