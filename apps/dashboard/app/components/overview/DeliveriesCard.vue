<script setup lang="ts">
import { ArrowRight } from '@lucide/vue'
import { Button, Card, CardAction, CardContent, CardHeader, CardTitle, Skeleton } from '@repo/ui'
import { formatAgo } from '@repo/utils'

const latest = useDeliveries({ limit: 5 })
const now = useNow()
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Deliveries</CardTitle>
      <CardAction>
        <Button variant="ghost" size="sm" as-child>
          <NuxtLink to="/deliveries">View all <ArrowRight /></NuxtLink>
        </Button>
      </CardAction>
    </CardHeader>
    <CardContent class="space-y-4">
      <DeliveryStatsSummary />
      <div>
        <h3 class="mb-2 text-xs font-medium text-muted-foreground">Latest</h3>
        <Skeleton v-if="latest.isPending.value" class="h-32" />
        <p v-else-if="latest.isError.value" class="text-sm text-destructive-foreground">
          {{ latest.error.value?.message }}
        </p>
        <p v-else-if="latest.data.value?.length === 0" class="text-sm text-muted-foreground">
          No deliveries — fire an event from the test panel.
        </p>
        <ul v-else class="divide-y">
          <li
            v-for="delivery in latest.data.value"
            :key="delivery.id"
            class="flex items-center gap-3 py-2"
          >
            <div class="min-w-0 flex-1">
              <p class="font-mono text-xs">{{ delivery.event_type }}</p>
              <p class="truncate font-mono text-xs text-muted-foreground">
                {{ delivery.endpoint_url }}
              </p>
            </div>
            <span class="text-xs text-muted-foreground">
              {{ formatAgo(delivery.updated_at, now) }}
            </span>
            <DeliveryStatusBadge :status="delivery.status" />
          </li>
        </ul>
      </div>
    </CardContent>
  </Card>
</template>
