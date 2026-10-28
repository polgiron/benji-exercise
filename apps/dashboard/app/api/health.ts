import { apiFetch } from './client'

export const getHealth = () => apiFetch<{ status: string }>('/api/health')
