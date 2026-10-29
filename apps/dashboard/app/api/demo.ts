import { apiFetch } from './client'
import type { IDemoReset, IDemoSeeded } from './types'

export const resetDemoData = () => apiFetch<IDemoReset>('/api/demo/reset', { method: 'POST' })

export const seedDemoData = () => apiFetch<IDemoSeeded>('/api/demo/seed', { method: 'POST' })
