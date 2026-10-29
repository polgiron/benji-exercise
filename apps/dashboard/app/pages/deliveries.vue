<script setup lang="ts">
import { PageHeader, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@repo/ui'
import { EDeliveryStatus, type IDeliveryFilters } from '~/api/types'
import { DELIVERY_STATUS_LABELS, isDeliveryStatus } from '~/utils/deliveryStatus'

// A Select item can't hold an empty value: this one stands for "no filter".
const ALL = 'all'

const route = useRoute()
const router = useRouter()
const endpoints = useEndpoints()

// The filters live in the URL, so a filtered view is a link.
const filters = computed<IDeliveryFilters>(() => ({
  status: isDeliveryStatus(route.query.status) ? route.query.status : undefined,
  endpointId: typeof route.query.endpoint_id === 'string' ? route.query.endpoint_id : undefined,
}))

function setFilter(name: 'status' | 'endpoint_id', value: unknown) {
  const query = { ...route.query, [name]: value === ALL ? undefined : String(value) }
  router.replace({ query })
}
</script>

<template>
  <section class="space-y-4">
    <PageHeader title="Deliveries">
      <Select
        :model-value="filters.status ?? ALL"
        @update:model-value="(value) => setFilter('status', value)"
      >
        <SelectTrigger class="w-40" aria-label="Filter by status"><SelectValue /></SelectTrigger>
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
        :model-value="filters.endpointId ?? ALL"
        @update:model-value="(value) => setFilter('endpoint_id', value)"
      >
        <SelectTrigger class="w-72" aria-label="Filter by endpoint"><SelectValue /></SelectTrigger>
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
    </PageHeader>
    <DeliveriesTable :filters="filters" @clear-filters="router.replace({ query: {} })" />
  </section>
</template>
