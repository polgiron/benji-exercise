import tailwindcss from '@tailwindcss/vite'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  // A live, client-side ops tool: nothing to gain from SSR here.
  ssr: false,
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
