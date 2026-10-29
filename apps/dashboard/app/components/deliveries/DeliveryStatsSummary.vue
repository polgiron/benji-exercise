<script setup lang="ts">
import { Skeleton, cn } from '@repo/ui'
import { EDeliveryStatus } from '~/api/types'
import { DELIVERY_STATUS_LABELS } from '~/utils/deliveryStatus'

interface Props {
  endpointId?: string
}

const props = defineProps<Props>()
const stats = useDeliveryStats(() => props.endpointId)

const ORDER = [
  EDeliveryStatus.PENDING,
  EDeliveryStatus.IN_PROGRESS,
  EDeliveryStatus.SUCCEEDED,
  EDeliveryStatus.FAILED,
]
</script>

<template>
  <Skeleton v-if="stats.isPending.value" class="h-14" />
  <p v-else-if="stats.isError.value" class="text-sm text-destructive-foreground">
    {{ stats.error.value?.message }}
  </p>
  <dl
    v-else-if="stats.data.value"
    class="grid grid-cols-[repeat(auto-fit,minmax(6.5rem,1fr))] gap-2"
  >
    <div v-for="status in ORDER" :key="status" class="rounded-md bg-muted/60 px-3 py-2">
      <dt class="text-2xs text-muted-foreground">{{ DELIVERY_STATUS_LABELS[status] }}</dt>
      <dd
        :class="
          cn('text-lg font-semibold tabular-nums', {
            'text-destructive-foreground':
              status === EDeliveryStatus.FAILED && stats.data.value[status] > 0,
          })
        "
      >
        {{ stats.data.value[status] }}
      </dd>
    </div>
    <div class="rounded-md bg-muted/60 px-3 py-2">
      <dt class="text-2xs text-muted-foreground">Total</dt>
      <dd class="text-lg font-semibold tabular-nums">{{ stats.data.value.total }}</dd>
    </div>
  </dl>
</template>
