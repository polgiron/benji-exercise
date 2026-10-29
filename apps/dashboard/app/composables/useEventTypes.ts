import { useQuery } from '@tanstack/vue-query'
import { listEventTypes } from '~/api/eventTypes'
import { eventTypeKeys } from './queryKeys'

export function useEventTypes() {
  // A catalogue seeded at API startup: it doesn't change while the dashboard is open.
  return useQuery({ queryKey: eventTypeKeys.all, queryFn: listEventTypes, staleTime: Infinity })
}
