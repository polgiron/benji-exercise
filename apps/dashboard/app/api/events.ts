import { apiFetch } from './client'
import type { IEventCreate, IEventPublished } from './types'

export const publishEvent = (body: IEventCreate, idempotencyKey: string) =>
  apiFetch<IEventPublished>('/api/events', {
    method: 'POST',
    body,
    headers: { 'Idempotency-Key': idempotencyKey },
  })
