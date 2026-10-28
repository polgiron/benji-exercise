import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

export default defineNuxtPlugin((nuxtApp) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: 1,
        // The SSE stream keeps data fresh; refetch on focus covers anything it missed.
        refetchOnWindowFocus: true,
      },
    },
  })

  nuxtApp.vueApp.use(VueQueryPlugin, { queryClient })
})
