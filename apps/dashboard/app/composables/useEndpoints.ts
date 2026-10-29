import { toast } from '@repo/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { createEndpoint, getEndpoint, listEndpoints, updateEndpoint } from '~/api/endpoints'
import type { IEndpointUpdate } from '~/api/types'
import { endpointKeys } from './queryKeys'

export function useEndpoints() {
  return useQuery({ queryKey: endpointKeys.list(), queryFn: listEndpoints })
}

export function useEndpoint(id: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => endpointKeys.detail(toValue(id))),
    queryFn: () => getEndpoint(toValue(id)),
  })
}

export function useCreateEndpoint() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createEndpoint,
    // The response carries the secret: refetch the list rather than seeding the cache with
    // it, and don't keep the finished mutation (and its data) around in the mutation cache.
    gcTime: 0,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: endpointKeys.all }),
    onError: (error) => toast.error(error.message),
  })
}

export function useUpdateEndpoint() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: IEndpointUpdate & { id: string }) => updateEndpoint(id, body),
    onSuccess: (endpoint) => {
      queryClient.setQueryData(endpointKeys.detail(endpoint.id), endpoint)
      return queryClient.invalidateQueries({ queryKey: endpointKeys.list() })
    },
    onError: (error) => toast.error(error.message),
  })
}
