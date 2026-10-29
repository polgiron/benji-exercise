import { toast } from '@repo/ui'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { resetDemoData, seedDemoData } from '~/api/demo'
import { deliveryKeys, endpointKeys } from './query-keys'

/** Both wipe the database: every endpoint and delivery the cache holds is gone. */
function useInvalidateAll() {
  const queryClient = useQueryClient()
  return () =>
    Promise.all(
      [endpointKeys.all, deliveryKeys.all].map((queryKey) =>
        queryClient.invalidateQueries({ queryKey }),
      ),
    )
}

export function useSeedDemo() {
  const invalidateAll = useInvalidateAll()
  return useMutation({
    mutationFn: seedDemoData,
    onSuccess: (seeded) => {
      toast.success(
        `Seeded ${seeded.endpoints} endpoints, ${seeded.events} events, ${seeded.deliveries} deliveries`,
      )
      return invalidateAll()
    },
    onError: (error) => toast.error(error.message),
  })
}

export function useResetDemo() {
  const invalidateAll = useInvalidateAll()
  return useMutation({
    mutationFn: resetDemoData,
    onSuccess: (deleted) => {
      toast.success(
        `Deleted ${deleted.endpoints} endpoints, ${deleted.events} events, ${deleted.deliveries} deliveries`,
      )
      return invalidateAll()
    },
    onError: (error) => toast.error(error.message),
  })
}
