import { toast } from '@repo/ui'
import { useMutation, useQuery } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { getDelivery, getDeliveryStats, listDeliveries, replayDelivery } from '~/api/deliveries'
import type { IDeliveryFilters } from '~/api/types'
import { deliveryKeys } from './queryKeys'
import { useDeliveryCache } from './useDeliveryCache'

export function useDeliveries(filters: MaybeRefOrGetter<IDeliveryFilters>) {
  return useQuery({
    queryKey: computed(() => deliveryKeys.list(toValue(filters))),
    queryFn: () => listDeliveries(toValue(filters)),
  })
}

export function useDelivery(id: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => deliveryKeys.detail(toValue(id))),
    queryFn: () => getDelivery(toValue(id)),
  })
}

export function useDeliveryStats(endpointId?: MaybeRefOrGetter<string | undefined>) {
  return useQuery({
    queryKey: computed(() => deliveryKeys.statsFor(toValue(endpointId))),
    queryFn: () => getDeliveryStats(toValue(endpointId)),
  })
}

export function useReplayDelivery() {
  const cache = useDeliveryCache()
  return useMutation({
    mutationFn: replayDelivery,
    // Same path as the stream, so whichever arrives second is dropped by its version.
    onSuccess: cache.apply,
    onError: (error) => toast.error(error.message),
  })
}
