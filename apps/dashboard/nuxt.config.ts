import tailwindcss from '@tailwindcss/vite'

// Runs in <head>, before the SPA's JS: puts the theme class on <html> from the choice
// theme-toggle.vue saved (useColorMode's default storage key) or the OS. Without it a dark
// reload shows a white page until the app boots.
const THEME_BOOT = `(() => {
  try {
    const saved = localStorage.getItem('vueuse-color-scheme')
    const dark = saved === 'dark' || ((!saved || saved === 'auto') && matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.classList.add(dark ? 'dark' : 'light')
  } catch {}
})()`

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: false },
  // A live, client-side ops tool: nothing to gain from SSR here.
  ssr: false,
  app: {
    head: {
      title: 'Benji Webhooks',
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
      script: [{ innerHTML: THEME_BOOT, tagPosition: 'head' }],
      // Until the stylesheet loads (in dev it arrives with the JS), let the browser paint its
      // own dark canvas.
      style: [{ innerHTML: 'html.dark { color-scheme: dark }' }],
    },
  },
  css: ['~/assets/css/main.css'],
  // Components are used by their file name (`<DeliveryRow />`), whatever folder they sit in.
  components: [{ path: '~/components', pathPrefix: false }],
  vite: {
    plugins: [tailwindcss()],
  },
  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000',
    },
  },
  devServer: {
    port: 3000,
  },
})
