<script setup lang="ts">
import { ArrowRight } from '@lucide/vue'
import { Skeleton, StatusDot, type StatusDotVariants } from '@repo/ui'

interface IHeroStatus {
  tone: StatusDotVariants['tone']
  pulse?: boolean
  text: string
  link?: { to: string; label: string }
}

const stats = useDeliveryStats()
const endpoints = useEndpoints()
const now = useNow()

const greeting = computed(() => {
  const hour = now.value.getHours()
  if (hour < 12) return 'Good morning'
  return hour < 18 ? 'Good afternoon' : 'Good evening'
})

// One line on how things stand, worst news first.
const status = computed<IHeroStatus | undefined>(() => {
  if (stats.isError.value || endpoints.isError.value) {
    return { tone: 'danger', text: 'Could not load the latest numbers.' }
  }
  const counts = stats.data.value
  if (!counts || !endpoints.data.value) return undefined
  if (endpoints.data.value.length === 0) {
    return { tone: 'muted', text: 'No endpoints yet: add one to start receiving events.' }
  }
  if (counts.failed > 0) {
    return {
      tone: 'danger',
      text: `${counts.failed} ${counts.failed === 1 ? 'delivery' : 'deliveries'} failed`,
      link: { to: '/deliveries?status=failed', label: 'Review' },
    }
  }
  const inFlight = counts.pending + counts.in_progress
  if (inFlight > 0) {
    return { tone: 'warning', pulse: true, text: `${inFlight} in flight, retries are on it` }
  }
  if (counts.total === 0) {
    return { tone: 'info', text: 'All set: fire a test event and watch it flow.' }
  }
  return { tone: 'success', text: 'All deliveries healthy' }
})
</script>

<template>
  <section>
    <p class="text-sm font-semibold text-primary">Overview</p>
    <h1 class="mt-1 text-3xl font-semibold tracking-tight">{{ greeting }}</h1>
    <div class="mt-2 flex h-6 items-center">
      <Skeleton v-if="!status" class="h-4 w-64" />
      <p v-else class="flex items-center gap-2 text-sm text-muted-foreground">
        <StatusDot :tone="status.tone" :pulse="status.pulse" />
        {{ status.text }}
        <NuxtLink
          v-if="status.link"
          :to="status.link.to"
          class="inline-flex items-center gap-1 font-medium text-primary hover:underline"
        >
          {{ status.link.label }} <ArrowRight class="size-3.5" />
        </NuxtLink>
      </p>
    </div>
  </section>
</template>
