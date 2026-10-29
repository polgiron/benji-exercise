<script setup lang="ts">
import { LoaderCircle } from '@lucide/vue'
import { Badge, cn } from '@repo/ui'
import { EDeliveryStatus } from '~/api/types'
import { DELIVERY_STATUS_LABELS, isDeliveryStatus } from '~/utils/deliveryStatus'

interface Props {
  status: string
}

const props = defineProps<Props>()
const status = computed(() => (isDeliveryStatus(props.status) ? props.status : undefined))
</script>

<template>
  <Badge
    variant="outline"
    :class="
      cn('border-transparent', {
        'bg-info/10 text-info-foreground': status === EDeliveryStatus.PENDING,
        'bg-warning/10 text-warning-foreground': status === EDeliveryStatus.IN_PROGRESS,
        'bg-success/10 text-success-foreground': status === EDeliveryStatus.SUCCEEDED,
        'bg-destructive/10 text-destructive-foreground': status === EDeliveryStatus.FAILED,
      })
    "
  >
    <LoaderCircle v-if="status === EDeliveryStatus.IN_PROGRESS" class="animate-spin" />
    {{ status ? DELIVERY_STATUS_LABELS[status] : props.status }}
  </Badge>
</template>
