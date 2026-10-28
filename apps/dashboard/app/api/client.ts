import { FetchError, type FetchOptions, ofetch } from 'ofetch'

/** The one error shape the UI deals with, whatever went wrong. */
export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status?: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/** Maps the API's `{ error: { code, message } }` body (or a network failure) to an ApiError. */
export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error
  if (error instanceof FetchError) {
    const body = error.data as { error?: { code?: string; message?: string } } | undefined
    if (body?.error?.message) {
      return new ApiError(body.error.code ?? 'error', body.error.message, error.statusCode)
    }
    if (!error.response) {
      return new ApiError('network_error', 'Could not reach the API. Is it running?')
    }
    return new ApiError('http_error', `Request failed (${error.statusCode})`, error.statusCode)
  }
  return new ApiError('unknown_error', 'Something went wrong.')
}

// Plain ofetch rather than Nuxt's `$fetch`, which is typed for Nuxt's own server routes.
export async function apiFetch<T>(path: string, options?: FetchOptions<'json'>): Promise<T> {
  const { apiBase } = useRuntimeConfig().public
  try {
    return await ofetch<T>(path, { baseURL: apiBase, ...options })
  } catch (error) {
    throw toApiError(error)
  }
}
