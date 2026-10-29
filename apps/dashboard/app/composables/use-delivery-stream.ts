import { createSharedComposable, useEventListener } from '@vueuse/core'
import { onScopeDispose, readonly, ref } from 'vue'
import { streamUrl } from '~/api/stream'
import type { IDeliverySummary } from '~/api/types'
import { useDeliveryCache } from './use-delivery-cache'

export enum EStreamState {
  CONNECTING = 'connecting',
  LIVE = 'live',
  RECONNECTING = 'reconnecting',
}

const RECONNECT_MS = 3000

/** The one SSE connection: delivery updates into the cache, and whether we are live. */
export const useDeliveryStream = createSharedComposable(() => {
  const cache = useDeliveryCache()
  const state = ref(EStreamState.CONNECTING)
  let source: EventSource | undefined
  let retry: ReturnType<typeof setTimeout> | undefined

  function connect() {
    source = new EventSource(streamUrl())
    source.addEventListener('ready', () => {
      state.value = EStreamState.LIVE
      cache.refetchAll()
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
    if (document.visibilityState === 'visible') cache.refetchAll()
  })
  onScopeDispose(() => {
    clearTimeout(retry)
    source?.close()
  })

  return { state: readonly(state) }
})
