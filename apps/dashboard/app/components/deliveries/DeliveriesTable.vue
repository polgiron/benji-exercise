<script setup lang="ts">
import {
  Button,
  Card,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableEmpty,
  TableHead,
  TableHeader,
  TableRow,
} from '@repo/ui'
import type { IDeliveryFilters } from '~/api/types'

interface Props {
  filters: IDeliveryFilters
  showEndpoint?: boolean
}

const props = withDefaults(defineProps<Props>(), { showEndpoint: true })
defineEmits<{ clearFilters: [] }>()

const deliveries = useDeliveries(() => props.filters)
const endpoints = useEndpoints()
const expandedId = ref<string>()
const columns = computed(() => (props.showEndpoint ? 7 : 6))
// Without the endpoint column, the endpoint filter is the page's scope, not the user's choice.
const isFiltered = computed(
  () => !!props.filters.status || (props.showEndpoint && !!props.filters.endpointId),
)
// The API refuses to replay into a paused endpoint: say so before the click, not after.
const pausedEndpointIds = computed(
  () => new Set(endpoints.data.value?.filter((e) => !e.enabled).map((e) => e.id)),
)

function toggle(id: string) {
  expandedId.value = expandedId.value === id ? undefined : id
}
</script>

<template>
  <Card class="gap-0 overflow-hidden py-0">
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Event type</TableHead>
          <TableHead v-if="showEndpoint">Endpoint</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Attempts</TableHead>
          <TableHead>Next retry</TableHead>
          <TableHead>Updated</TableHead>
          <TableHead><span class="sr-only">Actions</span></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <template v-if="deliveries.isPending.value">
          <TableRow v-for="n in 4" :key="n">
            <TableCell :colspan="columns"><Skeleton class="h-5" /></TableCell>
          </TableRow>
        </template>
        <TableEmpty v-else-if="deliveries.isError.value" :colspan="columns">
          <QueryError :query="deliveries" class="justify-center" />
        </TableEmpty>
        <TableEmpty v-else-if="deliveries.data.value?.length === 0" :colspan="columns">
          <span v-if="isFiltered" class="text-muted-foreground">
            No deliveries match these filters —
            <Button variant="link" size="inline" @click="$emit('clearFilters')">
              clear filters
            </Button>
          </span>
          <span v-else class="text-muted-foreground">
            No deliveries — fire an event from the test panel.
          </span>
        </TableEmpty>
        <DeliveryRow
          v-for="delivery in deliveries.data.value"
          v-else
          :key="delivery.id"
          :delivery="delivery"
          :expanded="expandedId === delivery.id"
          :show-endpoint="showEndpoint"
          :endpoint-paused="pausedEndpointIds.has(delivery.endpoint_id)"
          @toggle="toggle(delivery.id)"
        />
      </TableBody>
    </Table>
  </Card>
</template>
