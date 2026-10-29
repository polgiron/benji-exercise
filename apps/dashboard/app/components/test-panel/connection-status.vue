<script setup lang="ts">
import { StatusDot, type StatusDotVariants } from '@repo/ui'
import { EStreamState } from '~/composables/use-delivery-stream'

const { state } = useDeliveryStream()

const LABELS: Record<EStreamState, string> = {
  [EStreamState.CONNECTING]: 'Connecting…',
  [EStreamState.LIVE]: 'Live',
  [EStreamState.RECONNECTING]: 'Reconnecting…',
}

const TONES: Record<EStreamState, StatusDotVariants['tone']> = {
  [EStreamState.CONNECTING]: 'muted',
  [EStreamState.LIVE]: 'success',
  [EStreamState.RECONNECTING]: 'warning',
}
</script>

<template>
  <div
    class="flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium text-muted-foreground"
    :title="state === EStreamState.RECONNECTING ? 'The API may be down' : 'Updates stream in live'"
  >
    <StatusDot :tone="TONES[state]" :pulse="state !== EStreamState.CONNECTING" />
    {{ LABELS[state] }}
  </div>
</template>
