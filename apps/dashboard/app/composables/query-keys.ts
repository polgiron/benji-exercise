import type { EActivityRange, IDeliveryFilters } from '~/api/types'

export const endpointKeys = {
  all: ['endpoints'] as const,
  list: () => [...endpointKeys.all, 'list'] as const,
  detail: (id: string) => [...endpointKeys.all, 'detail', id] as const,
}

export const eventTypeKeys = {
  all: ['event-types'] as const,
}

export const deliveryKeys = {
  all: ['deliveries'] as const,
  lists: () => [...deliveryKeys.all, 'list'] as const,
  list: (filters: IDeliveryFilters) => [...deliveryKeys.lists(), filters] as const,
  details: () => [...deliveryKeys.all, 'detail'] as const,
  detail: (id: string) => [...deliveryKeys.details(), id] as const,
  stats: () => [...deliveryKeys.all, 'stats'] as const,
  statsFor: (endpointId?: string) => [...deliveryKeys.stats(), endpointId ?? 'all'] as const,
  // Under `stats`: whatever refreshes the counts after a status change refreshes the chart too.
  activity: (range: EActivityRange, endpointId?: string) =>
    [...deliveryKeys.stats(), 'activity', range, endpointId ?? 'all'] as const,
}
