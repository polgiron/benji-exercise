<script setup lang="ts">
import { ArrowRight, Send } from '@lucide/vue'
import {
  Button,
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
  Skeleton,
} from '@repo/ui'
import { formatAgo } from '@repo/utils'

const latest = useDeliveries({ limit: 5 })
const now = useNow()
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Latest deliveries</CardTitle>
      <CardDescription>Updates the moment they happen</CardDescription>
      <CardAction>
        <Button variant="ghost" size="sm" as-child>
          <NuxtLink to="/deliveries">View all <ArrowRight /></NuxtLink>
        </Button>
      </CardAction>
    </CardHeader>
    <CardContent>
      <ul v-if="latest.isPending.value" class="divide-y" aria-busy="true">
        <li v-for="n in 5" :key="n" class="flex items-center gap-3 py-3">
          <div class="flex-1 space-y-1.5">
            <Skeleton class="h-5 w-44" />
            <Skeleton class="h-3 w-56" />
          </div>
          <Skeleton class="h-5 w-20 rounded-full" />
        </li>
      </ul>
      <LoadError
        v-else-if="latest.isError.value"
        :message="latest.error.value?.message"
        @retry="latest.refetch()"
      />
      <Empty v-else-if="latest.data.value?.length === 0" class="p-4 md:p-8">
        <EmptyHeader>
          <EmptyMedia variant="glow"><Send /></EmptyMedia>
          <EmptyTitle class="text-base">No deliveries yet</EmptyTitle>
          <EmptyDescription>
            Fire an event from the test panel: it shows up here the moment it's queued.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
      <!-- New deliveries slide in at the top as the stream brings them. -->
      <TransitionGroup
        v-else
        tag="ul"
        class="divide-y"
        enter-from-class="opacity-0 -translate-y-2"
        enter-active-class="transition duration-500 ease-out-quart motion-reduce:transition-none"
        leave-active-class="hidden"
        move-class="transition duration-500 ease-out-quart"
      >
        <li
          v-for="delivery in latest.data.value"
          :key="delivery.id"
          class="flex items-center gap-3 py-3"
        >
          <div class="min-w-0 flex-1 space-y-1">
            <EventTypeBadge :type="delivery.event_type" />
            <p class="truncate font-mono text-xs text-muted-foreground">
              {{ delivery.endpoint_url }}
            </p>
          </div>
          <span class="shrink-0 text-xs text-muted-foreground">
            {{ formatAgo(delivery.updated_at, now) }}
          </span>
          <DeliveryStatusBadge :status="delivery.status" />
        </li>
      </TransitionGroup>
    </CardContent>
  </Card>
</template>
