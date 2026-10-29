<script setup lang="ts">
import { ChevronRight, LoaderCircle, RotateCcw } from '@lucide/vue'
import { Button, TableCell, TableRow, cn } from '@repo/ui'
import { formatAgo } from '@repo/utils'
import { EDeliveryStatus, type IDeliverySummary } from '~/api/types'
import { describeLastError } from '~/utils/delivery-status'

interface Props {
  delivery: IDeliverySummary
  expanded: boolean
  showEndpoint: boolean
}

const props = defineProps<Props>()
defineEmits<{ toggle: [] }>()

const replay = useReplayDelivery()
// A live update briefly tints the row, so a change catches the eye without being hunted for.
const flashing = ref(false)
watch(
  () => props.delivery.version,
  () => {
    flashing.value = false
    requestAnimationFrame(() => (flashing.value = true))
  },
)
const now = useNow()
const columns = computed(() => (props.showEndpoint ? 7 : 6))
</script>

<template>
  <TableRow
    :class="cn('cursor-pointer', { 'motion-safe:animate-flash': flashing })"
    :data-state="expanded ? 'selected' : undefined"
    :aria-expanded="expanded"
    @click="$emit('toggle')"
    @animationend="flashing = false"
  >
    <TableCell>
      <div class="flex items-center gap-2">
        <ChevronRight
          :class="
            cn('size-4 text-muted-foreground transition-transform', { 'rotate-90': expanded })
          "
        />
        <EventTypeBadge :type="delivery.event_type" />
      </div>
    </TableCell>
    <TableCell v-if="showEndpoint" class="max-w-64 truncate font-mono text-xs">
      {{ delivery.endpoint_url }}
    </TableCell>
    <TableCell>
      <div class="flex flex-col items-start gap-0.5">
        <DeliveryStatusBadge :status="delivery.status" />
        <span
          v-if="delivery.last_error && delivery.status !== EDeliveryStatus.SUCCEEDED"
          class="max-w-48 truncate text-xs text-muted-foreground"
          :title="delivery.last_error"
        >
          {{ describeLastError(delivery.last_error) }}
        </span>
      </div>
    </TableCell>
    <TableCell class="tabular-nums">
      {{ delivery.series_attempts }}/{{ delivery.max_attempts }}
      <span v-if="delivery.replay_count > 0" class="text-xs text-muted-foreground">
        · {{ delivery.replay_count }} {{ delivery.replay_count === 1 ? 'replay' : 'replays' }}
      </span>
    </TableCell>
    <TableCell>
      <RetryCountdown :status="delivery.status" :next-attempt-at="delivery.next_attempt_at" />
    </TableCell>
    <TableCell class="text-muted-foreground" :title="delivery.updated_at">
      {{ formatAgo(delivery.updated_at, now) }}
    </TableCell>
    <TableCell class="text-right">
      <Button
        v-if="delivery.status === EDeliveryStatus.FAILED"
        variant="outline"
        size="xs"
        :disabled="replay.isPending.value"
        @click.stop="replay.mutate(delivery.id)"
      >
        <LoaderCircle v-if="replay.isPending.value" class="animate-spin" />
        <RotateCcw v-else />
        Replay
      </Button>
    </TableCell>
  </TableRow>
  <TableRow v-if="expanded" class="hover:bg-transparent">
    <TableCell :colspan="columns" class="bg-muted/30 p-0">
      <DeliveryDetails :delivery="delivery" />
    </TableCell>
  </TableRow>
</template>
