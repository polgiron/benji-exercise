import { useQueryClient } from '@tanstack/vue-query'
import { createSharedComposable, useEventListener } from '@vueuse/core'
import { onScopeDispose, readonly, ref } from 'vue'
import { streamUrl } from '~/api/stream'
import type { IDeliverySummary } from '~/api/types'
import { useDeliveryCache } from './useDeliveryCache'

export enum EStreamState {
  CONNECTING = 'connecting',
  LIVE = 'live',
  RECONNECTING = 'reconnecting',
}

const RECONNECT_MS = 3000

/** The one SSE connection: delivery updates into the cache, and whether we are live. */
export const useDeliveryStream = createSharedComposable(() => {
  const queryClient = useQueryClient()
  const cache = useDeliveryCache()
  const state = ref(EStreamState.CONNECTING)
  let source: EventSource | undefined
  let retry: ReturnType<typeof setTimeout> | undefined

  // The stream has no backlog, and a reconnect may follow an API outage: refetch every active
  // query, not only deliveries, so views stuck on "could not reach the API" recover by
  // themselves. While the API is down, the reconnect loop below is what polls for it.
  const catchUp = () => queryClient.invalidateQueries()

  function connect() {
    source = new EventSource(streamUrl())
    source.addEventListener('ready', () => {
      state.value = EStreamState.LIVE
      catchUp()
    })
    source.addEventListener('delivery.updated', (message: MessageEvent<string>) => {
      cache.apply(JSON.parse(message.data) as IDeliverySummary)
    })
    source.addEventListener('error', () => {
      state.value = EStreamState.RECONNECTING
      // The browser retries a dropped stream by itself, but gives up for good on a failed
      // (re)connect, e.g. while the API is down.
      if (source?.readyState === EventSource.CLOSED) retry = setTimeout(connect, RECONNECT_MS)
    })
  }

  connect()
  useEventListener(document, 'visibilitychange', () => {
    if (document.visibilityState === 'visible') catchUp()
  })
  onScopeDispose(() => {
    clearTimeout(retry)
    source?.close()
  })

  return { state: readonly(state) }
})
