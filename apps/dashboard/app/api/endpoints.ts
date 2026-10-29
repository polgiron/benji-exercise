import { apiFetch } from './client'
import type { IEndpoint, IEndpointCreate, IEndpointCreated, IEndpointUpdate } from './types'

export const listEndpoints = () => apiFetch<IEndpoint[]>('/api/endpoints')

export const getEndpoint = (id: string) => apiFetch<IEndpoint>(`/api/endpoints/${id}`)

export const createEndpoint = (body: IEndpointCreate) =>
  apiFetch<IEndpointCreated>('/api/endpoints', { method: 'POST', body })

export const updateEndpoint = (id: string, body: IEndpointUpdate) =>
  apiFetch<IEndpoint>(`/api/endpoints/${id}`, { method: 'PATCH', body })
