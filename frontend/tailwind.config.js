import frappeUIPreset from 'frappe-ui/tailwind'

// Warm editorial palette — replaces the default cool-gray "template" look
// with parchment creams, warm inks and a terracotta accent.
const warmGray = {
  50: '#FBF9F4',
  100: '#F5F1E8',
  200: '#ECE5D6',
  300: '#DED2BC',
  400: '#C4B396',
  500: '#A18E6E',
  600: '#7D6C50',
  700: '#5E503B',
  800: '#43392B',
  900: '#2E271D',
  950: '#211B14',
}

// Terracotta / ember — primary accent color (replaces default blue scale)
const ember = {
  50: '#FBF2EC',
  100: '#F7E2D4',
  200: '#EFC6A9',
  300: '#E5A47A',
  400: '#DA7F4E',
  500: '#C75F2C',
  600: '#B04C21',
  700: '#8F3B1C',
  800: '#74301A',
  900: '#5F2A18',
}

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
  ],
  safelist: [{ pattern: /!(text|bg)-/, variants: ['hover', 'active'] }],
  theme: {
    extend: {
      colors: {
        gray: warmGray,
        blue: ember,
        // Semantic brand surfaces
        canvas: '#F4EDE1', // app background
        paper: '#FFFDF8', // card background
        linen: '#F8F2E6', // inset / subtle background
        hairline: '#E6DAC4', // card borders
        'hairline-strong': '#D5C5A7', // stronger borders
        ink: {
          DEFAULT: '#2A2318', // primary text
          soft: '#5C513D', // secondary text
          faint: '#94866A', // muted text
        },
        espresso: {
          DEFAULT: '#262013', // sidebar / dark surfaces
          soft: '#322A1B',
          line: '#3F3726',
          faint: '#6E624A',
        },
        creme: '#F3EAD8', // text on dark surfaces
      },
      fontFamily: {
        display: [
          'Iowan Old Style',
          'Palatino Linotype',
          'Book Antiqua',
          'Palatino',
          'URW Palladio L',
          'Georgia',
          'serif',
        ],
      },
      letterSpacing: {
        eyebrow: '0.14em',
      },
      maxWidth: {
        page: '78rem',
      },
    },
  },
  plugins: [],
}
