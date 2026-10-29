<script setup lang="ts">
import { ArrowRight, Plus, Webhook } from '@lucide/vue'
import {
  Button,
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  Skeleton,
  StatusDot,
  cn,
} from '@repo/ui'

const endpoints = useEndpoints()
const enabledCount = computed(() => endpoints.data.value?.filter((e) => e.enabled).length ?? 0)
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Endpoints</CardTitle>
      <CardDescription>
        <Skeleton v-if="endpoints.isPending.value" class="h-4 w-24" />
        <template v-else-if="endpoints.data.value">
          {{ enabledCount }} of {{ endpoints.data.value.length }} enabled
        </template>
      </CardDescription>
      <CardAction>
        <Button variant="ghost" size="sm" as-child>
          <NuxtLink to="/endpoints">View all <ArrowRight /></NuxtLink>
        </Button>
      </CardAction>
    </CardHeader>
    <CardContent>
      <ul v-if="endpoints.isPending.value" class="divide-y" aria-busy="true">
        <li v-for="n in 3" :key="n" class="space-y-2 py-3">
          <div class="flex items-center gap-2">
            <Skeleton class="size-2 rounded-full" />
            <Skeleton class="h-3.5 w-60" />
          </div>
          <div class="flex gap-1 pl-4">
            <Skeleton class="h-5 w-24" />
            <Skeleton class="h-5 w-28" />
          </div>
        </li>
      </ul>
      <LoadError
        v-else-if="endpoints.isError.value"
        :message="endpoints.error.value?.message"
        @retry="endpoints.refetch()"
      />
      <Empty v-else-if="endpoints.data.value?.length === 0" class="p-4 md:p-8">
        <EmptyHeader>
          <EmptyMedia variant="glow"><Webhook /></EmptyMedia>
          <EmptyTitle class="text-base">No endpoints yet</EmptyTitle>
          <EmptyDescription>
            Add the URL that should receive Benji events, and pick which ones it gets.
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button size="sm" as-child>
            <NuxtLink to="/endpoints?create"><Plus /> New endpoint</NuxtLink>
          </Button>
        </EmptyContent>
      </Empty>
      <ul v-else class="divide-y">
        <li
          v-for="endpoint in endpoints.data.value"
          :key="endpoint.id"
          :class="cn('space-y-1.5 py-3', { 'opacity-60': !endpoint.enabled })"
        >
          <div class="flex items-center gap-2">
            <StatusDot
              :tone="endpoint.enabled ? 'success' : 'muted'"
              :title="endpoint.enabled ? 'Enabled' : 'Paused'"
            />
            <NuxtLink
              :to="`/endpoints/${endpoint.id}`"
              class="block truncate font-mono text-xs font-medium hover:text-primary hover:underline"
            >
              {{ endpoint.url }}
            </NuxtLink>
          </div>
          <EventTypeChips :types="endpoint.event_types" class="pl-4" />
        </li>
      </ul>
    </CardContent>
  </Card>
</template>
