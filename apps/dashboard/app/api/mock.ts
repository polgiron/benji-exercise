// The worker POSTs to these, not the dashboard: it only needs their URLs to paste into an endpoint.
export const mockReceiverUrl = (pathAndQuery: string) =>
  `${useRuntimeConfig().public.apiBase}/mock/${pathAndQuery}`
