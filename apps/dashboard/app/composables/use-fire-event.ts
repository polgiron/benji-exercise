import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { ref, watch } from 'vue'
import { publishEvent } from '~/api/events'
import { deliveryKeys } from './query-keys'

export interface ISentEvent {
  eventType: string
  payload: Record<string, unknown>
  idempotencyKey: string
}

const newKey = () => crypto.randomUUID()

function parsePayload(text: string): Record<string, unknown> | string {
  try {
    const value: unknown = JSON.parse(text)
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      return value as Record<string, unknown>
    }
    return 'The payload must be a JSON object.'
  } catch (error) {
    return `Invalid JSON: ${(error as Error).message}`
  }
}

/**
 * The test panel's form. One idempotency key per intended action: a new one when the type
 * or the payload changes and after a send goes through; `resubmit` resends the last request
 * with its key, which is what makes the dedupe visible.
 */
export function useFireEvent() {
  const queryClient = useQueryClient()
  const eventType = ref('')
  const payloadText = ref('')
  const idempotencyKey = ref(newKey())
  const lastSent = ref<ISentEvent>()
  const parseError = ref<string>()

  watch([eventType, payloadText], () => {
    idempotencyKey.value = newKey()
    parseError.value = undefined
  })

  const mutation = useMutation({
    mutationFn: (event: ISentEvent) =>
      publishEvent({ event_type: event.eventType, payload: event.payload }, event.idempotencyKey),
    onSuccess: (_, event) => {
      lastSent.value = event
      // A network error keeps the key, so trying again is a safe retry, not a second event.
      if (event.idempotencyKey === idempotencyKey.value) idempotencyKey.value = newKey()
      return queryClient.invalidateQueries({ queryKey: deliveryKeys.all })
    },
  })

  function send() {
    const payload = parsePayload(payloadText.value)
    if (typeof payload === 'string') {
      parseError.value = payload
      return
    }
    mutation.mutate({ eventType: eventType.value, payload, idempotencyKey: idempotencyKey.value })
  }

  function resubmit() {
    if (lastSent.value) mutation.mutate(lastSent.value)
  }

  return {
    eventType,
    payloadText,
    idempotencyKey,
    lastSent,
    parseError,
    mutation,
    send,
    resubmit,
    regenerateKey: () => (idempotencyKey.value = newKey()),
  }
}
