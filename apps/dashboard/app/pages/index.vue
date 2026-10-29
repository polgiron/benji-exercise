<script setup lang="ts">
import { CircleCheck, Send, TriangleAlert, Webhook } from '@lucide/vue'
import { successRate } from '~/utils/delivery-status'

const stats = useDeliveryStats()
const endpoints = useEndpoints()

const enabledCount = computed(() => endpoints.data.value?.filter((e) => e.enabled).length ?? 0)
const rate = computed(() => stats.data.value && successRate(stats.data.value))
const percent = (value: number) => `${Math.round(value)}%`
</script>

<!-- Cards rise in one after the other; `motion-safe` leaves them still for reduced motion. -->
<template>
  <div class="space-y-6">
    <OverviewHero class="motion-safe:animate-rise" />
    <GettingStarted class="motion-safe:animate-rise motion-safe:[animation-delay:60ms]" />
    <ActivityCard class="motion-safe:animate-rise motion-safe:[animation-delay:120ms]" />

    <div class="grid gap-6 lg:grid-cols-12">
      <div class="grid grid-cols-2 gap-4 lg:col-span-5">
        <KpiCard
          label="Endpoints"
          :icon="Webhook"
          :value="endpoints.data.value?.length"
          :loading="endpoints.isPending.value"
          :hint="endpoints.data.value ? `${enabledCount} enabled` : undefined"
          to="/endpoints"
          class="motion-safe:animate-rise motion-safe:[animation-delay:180ms]"
        />
        <KpiCard
          label="Deliveries"
          :icon="Send"
          :value="stats.data.value?.total"
          :loading="stats.isPending.value"
          hint="All time"
          to="/deliveries"
          class="motion-safe:animate-rise motion-safe:[animation-delay:230ms]"
        />
        <KpiCard
          label="Success rate"
          :icon="CircleCheck"
          :value="rate"
          :loading="stats.isPending.value"
          :format="percent"
          :hint="
            rate === undefined ? 'Nothing settled yet' : `${stats.data.value?.succeeded} succeeded`
          "
          class="motion-safe:animate-rise motion-safe:[animation-delay:280ms]"
        />
        <KpiCard
          label="Failed"
          :icon="TriangleAlert"
          :value="stats.data.value?.failed"
          :loading="stats.isPending.value"
          :danger="!!stats.data.value?.failed"
          :hint="stats.data.value?.failed ? 'Waiting for a replay' : 'Nothing to fix'"
          to="/deliveries?status=failed"
          class="motion-safe:animate-rise motion-safe:[animation-delay:330ms]"
        />
      </div>
      <BreakdownCard
        class="lg:col-span-7 motion-safe:animate-rise motion-safe:[animation-delay:230ms]"
      />
    </div>

    <div class="grid gap-6 xl:grid-cols-2">
      <DeliveriesCard class="motion-safe:animate-rise motion-safe:[animation-delay:380ms]" />
      <EndpointsCard class="motion-safe:animate-rise motion-safe:[animation-delay:430ms]" />
    </div>
  </div>
</template>
