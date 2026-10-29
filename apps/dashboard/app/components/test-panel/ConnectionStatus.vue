<script setup lang="ts">
import { cn } from '@repo/ui'
import { EStreamState } from '~/composables/useDeliveryStream'

const { state } = useDeliveryStream()

const LABELS: Record<EStreamState, string> = {
  [EStreamState.CONNECTING]: 'Connecting…',
  [EStreamState.LIVE]: 'Live',
  [EStreamState.RECONNECTING]: 'Reconnecting…',
}
</script>

<template>
  <div class="flex items-center gap-2 text-xs text-muted-foreground">
    <span
      :class="
        cn('size-2 rounded-full', {
          'bg-success': state === EStreamState.LIVE,
          'animate-pulse bg-warning': state === EStreamState.RECONNECTING,
          'bg-muted-foreground': state === EStreamState.CONNECTING,
        })
      "
    />
    {{ LABELS[state] }}
    <span v-if="state === EStreamState.RECONNECTING">— the API may be down</span>
  </div>
</template>
