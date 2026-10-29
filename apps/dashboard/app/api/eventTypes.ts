import { apiFetch } from './client'
import type { IEventType } from './types'

export const listEventTypes = () => apiFetch<IEventType[]>('/api/event-types')
