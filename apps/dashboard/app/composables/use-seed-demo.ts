import { toast } from '@repo/ui'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { seedDemoData } from '~/api/demo'
import { deliveryKeys, endpointKeys } from './query-keys'

export function useSeedDemo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: seedDemoData,
    onSuccess: (seeded) => {
      toast.success(
        `Seeded ${seeded.endpoints} endpoints, ${seeded.events} events, ${seeded.deliveries} deliveries`,
      )
      // Every endpoint and delivery the cache holds was just deleted.
      return Promise.all(
        [endpointKeys.all, deliveryKeys.all].map((queryKey) =>
          queryClient.invalidateQueries({ queryKey }),
        ),
      )
    },
    onError: (error) => toast.error(error.message),
  })
}
