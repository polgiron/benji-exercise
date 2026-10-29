<script setup lang="ts">
import { ArrowRight, ChartPie } from '@lucide/vue'
import {
  AnimatedNumber,
  Badge,
  Button,
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle,
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  Skeleton,
  StatusDot,
  cn,
  type StatusDotVariants,
} from '@repo/ui'
import { EDeliveryStatus } from '~/api/types'
import { DELIVERY_STATUS_LABELS, successRate } from '~/utils/delivery-status'

const stats = useDeliveryStats()

const SEGMENTS: { status: EDeliveryStatus; bar: string; tone: StatusDotVariants['tone'] }[] = [
  { status: EDeliveryStatus.SUCCEEDED, bar: 'bg-success', tone: 'success' },
  { status: EDeliveryStatus.IN_PROGRESS, bar: 'bg-warning', tone: 'warning' },
  { status: EDeliveryStatus.PENDING, bar: 'bg-info', tone: 'info' },
  { status: EDeliveryStatus.FAILED, bar: 'bg-destructive', tone: 'danger' },
]

const rate = computed(() => stats.data.value && successRate(stats.data.value))
const share = (count: number) =>
  stats.data.value?.total ? Math.round((count / stats.data.value.total) * 100) : 0
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Breakdown</CardTitle>
      <CardAction>
        <Button variant="ghost" size="sm" as-child>
          <NuxtLink to="/deliveries">View all <ArrowRight /></NuxtLink>
        </Button>
      </CardAction>
    </CardHeader>
    <CardContent class="flex flex-1 flex-col">
      <div v-if="stats.isPending.value" class="space-y-4" aria-busy="true">
        <Skeleton class="h-4 w-24" />
        <Skeleton class="h-10 w-36" />
        <Skeleton class="h-2.5 w-full rounded-full" />
        <div class="space-y-3 pt-4">
          <Skeleton v-for="n in 4" :key="n" class="h-5" />
        </div>
      </div>
      <LoadError
        v-else-if="stats.isError.value"
        :message="stats.error.value?.message"
        @retry="stats.refetch()"
      />
      <Empty v-else-if="stats.data.value?.total === 0" class="p-4 md:p-6">
        <EmptyHeader>
          <EmptyMedia variant="glow"><ChartPie /></EmptyMedia>
          <EmptyTitle class="text-base">Nothing to break down yet</EmptyTitle>
          <EmptyDescription>
            Every delivery ends up succeeded, retrying or failed. Fire an event to see the split.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
      <template v-else-if="stats.data.value">
        <p class="text-sm text-muted-foreground">All deliveries</p>
        <div class="mt-1 flex items-center gap-3">
          <span class="text-4xl font-semibold tracking-tight">
            <AnimatedNumber :value="stats.data.value.total" />
          </span>
          <Badge v-if="rate !== undefined" variant="success">
            {{ Math.round(rate) }}% delivered
          </Badge>
        </div>
        <!-- One bar per status, sized by its count; `flex-grow` animates as counts move. -->
        <div class="mt-5 flex h-2.5 gap-1" aria-hidden="true">
          <div
            v-for="segment in SEGMENTS"
            v-show="stats.data.value[segment.status] > 0"
            :key="segment.status"
            :class="
              cn('rounded-full transition-[flex-grow] duration-700 ease-out-quart', segment.bar)
            "
            :style="{ flexGrow: stats.data.value[segment.status] }"
          />
        </div>
        <ul class="mt-6 divide-y border-t">
          <li
            v-for="segment in SEGMENTS"
            :key="segment.status"
            class="flex items-center gap-3 py-3"
          >
            <StatusDot :tone="segment.tone" />
            <span class="text-sm">{{ DELIVERY_STATUS_LABELS[segment.status] }}</span>
            <span class="ml-auto text-sm font-semibold tabular-nums">
              <AnimatedNumber :value="stats.data.value[segment.status]" />
            </span>
            <span class="w-10 text-right text-xs text-muted-foreground tabular-nums">
              {{ share(stats.data.value[segment.status]) }}%
            </span>
          </li>
        </ul>
      </template>
    </CardContent>
  </Card>
</template>
