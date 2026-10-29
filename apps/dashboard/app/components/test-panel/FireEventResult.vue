<script setup lang="ts">
import { Alert, AlertDescription, AlertTitle, type AlertVariants } from '@repo/ui'
import type { ApiError } from '~/api/client'
import type { IEventPublished } from '~/api/types'

interface Props {
  parseError?: string
  error: ApiError | null
  result?: IEventPublished
}

const props = defineProps<Props>()

const banner = computed<{
  variant: AlertVariants['variant']
  title: string
  detail: string
} | null>(() => {
  if (props.parseError) {
    return { variant: 'destructive', title: 'Not sent', detail: props.parseError }
  }
  if (props.error) {
    switch (props.error.code) {
      case 'invalid_payload':
        return {
          variant: 'destructive',
          title: 'Rejected: the payload breaks the schema',
          detail: props.error.message,
        }
      case 'idempotency_key_reused':
        return {
          variant: 'destructive',
          title: 'Key already used for a different payload',
          detail: 'A key stands for one action. Generate a new key to send this payload.',
        }
      default:
        return { variant: 'destructive', title: 'Not sent', detail: props.error.message }
    }
  }
  if (!props.result) return null
  const { event, delivery_count: count } = props.result
  if (props.result.deduplicated) {
    return {
      variant: 'info',
      title: 'Deduplicated',
      detail: `Already received as ${event.id}: no new deliveries.`,
    }
  }
  return {
    variant: 'success',
    title: `Created ${event.id}`,
    detail:
      count > 0
        ? `${count} ${count === 1 ? 'delivery' : 'deliveries'} queued.`
        : 'No enabled endpoint is subscribed to this type: nothing to deliver.',
  }
})
</script>

<template>
  <Alert v-if="banner" :variant="banner.variant" role="status">
    <AlertTitle>{{ banner.title }}</AlertTitle>
    <AlertDescription>{{ banner.detail }}</AlertDescription>
  </Alert>
</template>
