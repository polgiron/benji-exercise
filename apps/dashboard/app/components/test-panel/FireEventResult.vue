<script setup lang="ts">
import { cn } from '@repo/ui'
import type { ApiError } from '~/api/client'
import type { IEventPublished } from '~/api/types'

interface Props {
  parseError?: string
  error: ApiError | null
  result?: IEventPublished
}

const props = defineProps<Props>()

const banner = computed(() => {
  if (props.parseError) return { tone: 'error', title: 'Not sent', detail: props.parseError }
  if (props.error) {
    switch (props.error.code) {
      case 'invalid_payload':
        return {
          tone: 'error',
          title: 'Rejected: the payload breaks the schema',
          detail: props.error.message,
        }
      case 'idempotency_key_reused':
        return {
          tone: 'error',
          title: 'Key already used for a different payload',
          detail: 'A key stands for one action. Generate a new key to send this payload.',
        }
      default:
        return { tone: 'error', title: 'Not sent', detail: props.error.message }
    }
  }
  if (!props.result) return null
  const { event, delivery_count: count } = props.result
  if (props.result.deduplicated) {
    return {
      tone: 'info',
      title: 'Deduplicated',
      detail: `Already received as ${event.id}: no new deliveries.`,
    }
  }
  return {
    tone: 'success',
    title: `Created ${event.id}`,
    detail:
      count > 0
        ? `${count} ${count === 1 ? 'delivery' : 'deliveries'} queued.`
        : 'No enabled endpoint is subscribed to this type: nothing to deliver.',
  }
})
</script>

<template>
  <div
    v-if="banner"
    role="status"
    :class="
      cn('rounded-md px-3 py-2 text-xs', {
        'bg-destructive/10 text-destructive-foreground': banner.tone === 'error',
        'bg-info/10 text-info-foreground': banner.tone === 'info',
        'bg-success/10 text-success-foreground': banner.tone === 'success',
      })
    "
  >
    <p class="font-medium">{{ banner.title }}</p>
    <p class="break-words">{{ banner.detail }}</p>
  </div>
</template>
