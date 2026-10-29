<script setup lang="ts">
import { LoaderCircle } from '@lucide/vue'
import { Badge, type BadgeVariants } from '@repo/ui'
import { EDeliveryStatus } from '~/api/types'
import { DELIVERY_STATUS_LABELS, isDeliveryStatus } from '~/utils/deliveryStatus'

interface Props {
  status: string
}

const props = defineProps<Props>()

const VARIANTS: Record<EDeliveryStatus, BadgeVariants['variant']> = {
  [EDeliveryStatus.PENDING]: 'info',
  [EDeliveryStatus.IN_PROGRESS]: 'warning',
  [EDeliveryStatus.SUCCEEDED]: 'success',
  [EDeliveryStatus.FAILED]: 'danger',
}

const status = computed(() => (isDeliveryStatus(props.status) ? props.status : undefined))
</script>

<template>
  <Badge :variant="status ? VARIANTS[status] : 'outline'">
    <LoaderCircle v-if="status === EDeliveryStatus.IN_PROGRESS" class="animate-spin" />
    {{ status ? DELIVERY_STATUS_LABELS[status] : props.status }}
  </Badge>
</template>
