import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiFetch } from './client'
import { getDeliveryStats, listDeliveries, replayDelivery } from './deliveries'
import { createEndpoint, updateEndpoint } from './endpoints'
import { publishEvent } from './events'
import { EDeliveryStatus } from './types'

vi.mock('./client', () => ({ apiFetch: vi.fn() }))

describe('API functions build the right request', () => {
  beforeEach(() => vi.mocked(apiFetch).mockClear())

  it('lists deliveries with the filters as snake_case query params', () => {
    listDeliveries({ status: EDeliveryStatus.FAILED, endpointId: 'ep_1', limit: 5 })
    expect(apiFetch).toHaveBeenCalledWith('/api/deliveries', {
      query: { status: 'failed', endpoint_id: 'ep_1', limit: 5 },
    })
  })

  it('scopes stats to an endpoint', () => {
    getDeliveryStats('ep_1')
    expect(apiFetch).toHaveBeenCalledWith('/api/deliveries/stats', {
      query: { endpoint_id: 'ep_1' },
    })
  })

  it('replays with a POST', () => {
    replayDelivery('dlv_1')
    expect(apiFetch).toHaveBeenCalledWith('/api/deliveries/dlv_1/replay', { method: 'POST' })
  })

  it('creates and patches endpoints', () => {
    const body = { url: 'http://localhost:8000/mock/ok', event_types: ['campaign_updated'] }
    createEndpoint(body)
    updateEndpoint('ep_1', { enabled: false })
    expect(apiFetch).toHaveBeenNthCalledWith(1, '/api/endpoints', { method: 'POST', body })
    expect(apiFetch).toHaveBeenNthCalledWith(2, '/api/endpoints/ep_1', {
      method: 'PATCH',
      body: { enabled: false },
    })
  })

  it('sends the idempotency key as a header', () => {
    publishEvent({ event_type: 'campaign_updated', payload: {} }, 'key-1')
    expect(apiFetch).toHaveBeenCalledWith('/api/events', {
      method: 'POST',
      body: { event_type: 'campaign_updated', payload: {} },
      headers: { 'Idempotency-Key': 'key-1' },
    })
  })
})
