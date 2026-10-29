<script setup lang="ts">
import { EDeliveryStatus } from '~/api/types'

interface Props {
  status: string
  nextAttemptAt: string | null
}

const props = defineProps<Props>()
const now = useNow()

// Derived from `next_attempt_at` and the shared clock: the stream never pushes a tick.
const seconds = computed(() => {
  if (props.status !== EDeliveryStatus.PENDING || !props.nextAttemptAt) return null
  return Math.ceil((new Date(props.nextAttemptAt).getTime() - now.value.getTime()) / 1000)
})
</script>

<template>
  <span v-if="seconds === null" class="text-muted-foreground">—</span>
  <span v-else-if="seconds > 0" class="tabular-nums">in {{ seconds }} s</span>
  <span v-else class="text-muted-foreground">due now</span>
</template>
