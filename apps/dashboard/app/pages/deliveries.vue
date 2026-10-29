<script setup lang="ts">
import { X } from '@lucide/vue'
import {
  Button,
  PageHeader,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@repo/ui'
import { EDeliveryStatus, type IDeliveryFilters } from '~/api/types'
import { DELIVERY_STATUS_LABELS, isDeliveryStatus } from '~/utils/delivery-status'

// A Select item can't hold an empty value: this one stands for "no filter".
const ALL = 'all'

const route = useRoute()
const router = useRouter()
const endpoints = useEndpoints()
const eventTypes = useEventTypes()

// The filters live in the URL, so a filtered view is a link.
const filters = computed<IDeliveryFilters>(() => ({
  status: isDeliveryStatus(route.query.status) ? route.query.status : undefined,
  eventType: typeof route.query.event_type === 'string' ? route.query.event_type : undefined,
  endpointId: typeof route.query.endpoint_id === 'string' ? route.query.endpoint_id : undefined,
}))
const filtered = computed(
  () => !!filters.value.status || !!filters.value.eventType || !!filters.value.endpointId,
)

function setFilter(name: 'status' | 'event_type' | 'endpoint_id', value: unknown) {
  const query = { ...route.query, [name]: value === ALL ? undefined : String(value) }
  router.replace({ query })
}
</script>

<template>
  <section class="space-y-4">
    <PageHeader
      title="Deliveries"
      description="Every attempt to reach an endpoint, its retries and replays. Live."
    />

    <div class="flex flex-wrap items-center gap-3">
      <Select
        :model-value="filters.status ?? ALL"
        @update:model-value="(value) => setFilter('status', value)"
      >
        <SelectTrigger class="w-full sm:w-44" aria-label="Filter by status">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem :value="ALL">All statuses</SelectItem>
          <SelectItem
            v-for="status in Object.values(EDeliveryStatus)"
            :key="status"
            :value="status"
          >
            {{ DELIVERY_STATUS_LABELS[status] }}
          </SelectItem>
        </SelectContent>
      </Select>
      <Select
        :model-value="filters.eventType ?? ALL"
        @update:model-value="(value) => setFilter('event_type', value)"
      >
        <SelectTrigger class="w-full sm:w-72" aria-label="Filter by event type">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem :value="ALL">All event types</SelectItem>
          <SelectItem v-for="type in eventTypes.data.value" :key="type.key" :value="type.key">
            <EventTypeBadge :type="type.key" />
          </SelectItem>
        </SelectContent>
      </Select>
      <Select
        :model-value="filters.endpointId ?? ALL"
        @update:model-value="(value) => setFilter('endpoint_id', value)"
      >
        <SelectTrigger class="w-full min-w-0 sm:flex-1" aria-label="Filter by endpoint">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem :value="ALL">All endpoints</SelectItem>
          <SelectItem
            v-for="endpoint in endpoints.data.value"
            :key="endpoint.id"
            :value="endpoint.id"
          >
            <span class="font-mono text-xs">{{ endpoint.url }}</span>
          </SelectItem>
        </SelectContent>
      </Select>
      <Button v-if="filtered" variant="ghost" size="sm" as-child>
        <NuxtLink :to="{ query: {} }"><X /> Clear</NuxtLink>
      </Button>
    </div>

    <DeliveriesTable :filters="filters" />
  </section>
</template>
