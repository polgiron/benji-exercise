<script setup lang="ts">
import { Skeleton, Stat, StatGrid } from '@repo/ui'
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
  <StatGrid v-else-if="stats.data.value">
    <Stat
      v-for="status in ORDER"
      :key="status"
      :label="DELIVERY_STATUS_LABELS[status]"
      :value="stats.data.value[status]"
      :tone="
        status === EDeliveryStatus.FAILED && stats.data.value[status] > 0 ? 'danger' : 'default'
      "
    />
    <Stat label="Total" :value="stats.data.value.total" />
  </StatGrid>
</template>
