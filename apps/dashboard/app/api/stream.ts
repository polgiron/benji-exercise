// EventSource opens its own connection, so this is a URL rather than an apiFetch call.
export const streamUrl = () => `${useRuntimeConfig().public.apiBase}/api/stream`
