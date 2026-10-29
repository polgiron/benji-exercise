import { apiFetch } from './client'
import type { IDemoSeeded } from './types'

export const seedDemoData = () => apiFetch<IDemoSeeded>('/api/demo/seed', { method: 'POST' })
