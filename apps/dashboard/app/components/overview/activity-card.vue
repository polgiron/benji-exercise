<script setup lang="ts">
import { Activity } from '@lucide/vue'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
} from '@repo/ui'
import { EActivityRange } from '~/api/types'
import { ACTIVITY_BUCKET_LABELS, ACTIVITY_RANGE_LABELS, isActivityRange } from '~/utils/activity'

const range = ref(EActivityRange.WEEK)
const activity = useDeliveryActivity(range)

const totals = computed(() =>
  (activity.data.value?.buckets ?? []).reduce(
    (sum, bucket) => ({ total: sum.total + bucket.total, failed: sum.failed + bucket.failed }),
    { total: 0, failed: 0 },
  ),
)
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Activity</CardTitle>
      <CardDescription>Deliveries created {{ ACTIVITY_BUCKET_LABELS[range] }}</CardDescription>
      <CardAction>
        <Select
          :model-value="range"
          @update:model-value="(value) => isActivityRange(value) && (range = value)"
        >
          <SelectTrigger class="w-40" aria-label="Time range"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem
              v-for="option in Object.values(EActivityRange)"
              :key="option"
              :value="option"
            >
              {{ ACTIVITY_RANGE_LABELS[option] }}
            </SelectItem>
          </SelectContent>
        </Select>
      </CardAction>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm text-muted-foreground">
        <span class="flex items-center gap-2">
          <span class="size-2.5 rounded-full bg-chart-1" /> Deliveries
          <Skeleton v-if="activity.isPending.value" class="h-4 w-8" />
          <span v-else class="font-semibold text-foreground tabular-nums">{{ totals.total }}</span>
        </span>
        <span class="flex items-center gap-2">
          <span class="size-2.5 rounded-full bg-chart-4" /> Failed
          <Skeleton v-if="activity.isPending.value" class="h-4 w-8" />
          <span v-else class="font-semibold text-foreground tabular-nums">{{ totals.failed }}</span>
        </span>
      </div>

      <!-- Loading: the chart's own frame, axes and all, so nothing jumps when it lands. -->
      <div v-if="activity.isPending.value" class="flex h-64 gap-3" aria-busy="true">
        <div class="flex w-10 flex-col items-end justify-between pb-6">
          <Skeleton v-for="n in 5" :key="n" class="h-3 w-6" />
        </div>
        <div class="flex flex-1 flex-col gap-3">
          <Skeleton class="flex-1 rounded-lg" />
          <div class="flex justify-between">
            <Skeleton v-for="n in 7" :key="n" class="h-3 w-10" />
          </div>
        </div>
      </div>
      <LoadError
        v-else-if="activity.isError.value"
        :message="activity.error.value?.message"
        @retry="activity.refetch()"
      />
      <div v-else-if="activity.data.value" class="relative">
        <ActivityChart
          :activity="activity.data.value"
          :class="{ 'opacity-30 blur-[1px]': totals.total === 0 }"
        />
        <Empty
          v-if="totals.total === 0"
          class="absolute inset-0 justify-center p-0 pb-6 md:p-0 md:pb-6"
        >
          <EmptyHeader>
            <EmptyMedia variant="glow"><Activity /></EmptyMedia>
            <EmptyTitle class="text-base">Quiet so far</EmptyTitle>
            <EmptyDescription>
              No deliveries in the {{ ACTIVITY_RANGE_LABELS[range].toLowerCase() }}. Fire an event
              from the test panel and it shows up here.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      </div>
    </CardContent>
  </Card>
</template>
