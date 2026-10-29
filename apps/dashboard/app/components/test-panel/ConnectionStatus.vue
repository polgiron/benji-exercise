<script setup lang="ts">
import { StatusDot, type StatusDotVariants } from '@repo/ui'
import { EStreamState } from '~/composables/useDeliveryStream'

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
  <div class="flex items-center gap-2 text-xs text-muted-foreground">
    <StatusDot :tone="TONES[state]" :pulse="state === EStreamState.RECONNECTING" />
    {{ LABELS[state] }}
    <span v-if="state === EStreamState.RECONNECTING">— the API may be down</span>
  </div>
</template>
