import { FetchError } from 'ofetch'
import { describe, expect, it } from 'vitest'
import { ApiError, toApiError } from './client'

function fetchError(status: number, data?: unknown) {
  const error = new FetchError('failed')
  Object.assign(error, { response: { status }, statusCode: status, data })
  return error
}

describe('toApiError', () => {
  it('uses the API error body when present', () => {
    const error = toApiError(fetchError(409, { error: { code: 'not_replayable', message: 'Only failed deliveries can be replayed' } }))
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ code: 'not_replayable', status: 409 })
  })

  it('reports an unreachable API as a network error', () => {
    expect(toApiError(new FetchError('fetch failed')).code).toBe('network_error')
  })
})
