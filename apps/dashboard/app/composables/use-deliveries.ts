import { toast } from '@repo/ui'
import { keepPreviousData, useMutation, useQuery } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import {
  getDelivery,
  getDeliveryActivity,
  getDeliveryStats,
  listDeliveries,
  replayDelivery,
} from '~/api/deliveries'
import type { EActivityRange, IDeliveryFilters } from '~/api/types'
import { deliveryKeys } from './query-keys'
import { useDeliveryCache } from './use-delivery-cache'

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

export function useDeliveryActivity(
  range: MaybeRefOrGetter<EActivityRange>,
  endpointId?: MaybeRefOrGetter<string | undefined>,
) {
  return useQuery({
    queryKey: computed(() => deliveryKeys.activity(toValue(range), toValue(endpointId))),
    queryFn: () => getDeliveryActivity(toValue(range), toValue(endpointId)),
    // Switching range keeps the old curve up until the new one lands, instead of a skeleton.
    placeholderData: keepPreviousData,
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
