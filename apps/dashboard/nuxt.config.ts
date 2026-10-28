import tailwindcss from '@tailwindcss/vite'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  // A live, client-side ops tool: nothing to gain from SSR here.
  ssr: false,
  modules: ['shadcn-nuxt'],
  css: ['~/assets/css/main.css'],
  vite: {
    plugins: [tailwindcss()],
  },
  shadcn: {
    prefix: '',
    componentDir: './app/components/ui',
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
