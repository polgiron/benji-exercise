<script setup lang="ts">
import { Search, Send } from '@lucide/vue'
import {
  Button,
  Card,
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
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
const deliveries = useDeliveries(() => props.filters)
const endpoints = useEndpoints()
const expandedId = ref<string>()
const columns = computed(() => (props.showEndpoint ? 7 : 6))
// A filter the user picked, as opposed to the endpoint a detail page pins.
const filtered = computed(
  () =>
    !!props.filters.status ||
    !!props.filters.eventType ||
    (props.showEndpoint && !!props.filters.endpointId),
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
        <!-- Loading: one skeleton per cell, shaped like what lands there. -->
        <template v-if="deliveries.isPending.value">
          <TableRow v-for="n in 6" :key="n" class="hover:bg-transparent" aria-busy="true">
            <TableCell>
              <div class="flex items-center gap-2">
                <Skeleton class="size-4" />
                <Skeleton class="h-3.5 w-32" />
              </div>
            </TableCell>
            <TableCell v-if="showEndpoint"><Skeleton class="h-3.5 w-48" /></TableCell>
            <TableCell><Skeleton class="h-5 w-20 rounded-full" /></TableCell>
            <TableCell><Skeleton class="h-3.5 w-8" /></TableCell>
            <TableCell><Skeleton class="h-3.5 w-14" /></TableCell>
            <TableCell><Skeleton class="h-3.5 w-20" /></TableCell>
            <TableCell />
          </TableRow>
        </template>
        <TableEmpty
          v-else-if="deliveries.isError.value"
          :colspan="columns"
          class="whitespace-normal"
        >
          <LoadError :message="deliveries.error.value?.message" @retry="deliveries.refetch()" />
        </TableEmpty>
        <TableEmpty
          v-else-if="deliveries.data.value?.length === 0"
          :colspan="columns"
          class="whitespace-normal"
        >
          <Empty v-if="filtered" class="p-4 md:p-8">
            <EmptyHeader>
              <EmptyMedia variant="glow"><Search /></EmptyMedia>
              <EmptyTitle class="text-base">No deliveries match</EmptyTitle>
              <EmptyDescription>Try another status, event type or endpoint.</EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
              <Button variant="outline" size="sm" as-child>
                <NuxtLink :to="{ query: {} }">Clear filters</NuxtLink>
              </Button>
            </EmptyContent>
          </Empty>
          <Empty v-else class="p-4 md:p-8">
            <EmptyHeader>
              <EmptyMedia variant="glow"><Send /></EmptyMedia>
              <EmptyTitle class="text-base">
                {{ showEndpoint ? 'No deliveries yet' : 'Nothing delivered here yet' }}
              </EmptyTitle>
              <EmptyDescription>
                <template v-if="showEndpoint">
                  Fire an event from the test panel: every delivery, retry and replay shows up here,
                  live.
                </template>
                <template v-else>
                  Events this endpoint subscribes to land here as soon as they're fired.
                </template>
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
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
