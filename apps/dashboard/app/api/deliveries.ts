import { apiFetch } from './client'
import type { IDeliveryDetail, IDeliveryFilters, IDeliveryStats, IDeliverySummary } from './types'

export const listDeliveries = ({ status, endpointId, limit }: IDeliveryFilters = {}) =>
  apiFetch<IDeliverySummary[]>('/api/deliveries', {
    query: { status, endpoint_id: endpointId, limit },
  })

export const getDelivery = (id: string) => apiFetch<IDeliveryDetail>(`/api/deliveries/${id}`)

export const getDeliveryStats = (endpointId?: string) =>
  apiFetch<IDeliveryStats>('/api/deliveries/stats', { query: { endpoint_id: endpointId } })

export const replayDelivery = (id: string) =>
  apiFetch<IDeliverySummary>(`/api/deliveries/${id}/replay`, { method: 'POST' })
