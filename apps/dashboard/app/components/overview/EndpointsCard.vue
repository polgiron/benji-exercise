<script setup lang="ts">
import { ArrowRight } from '@lucide/vue'
import {
  Button,
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Skeleton,
  cn,
} from '@repo/ui'

const endpoints = useEndpoints()
const enabledCount = computed(() => endpoints.data.value?.filter((e) => e.enabled).length ?? 0)
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Endpoints</CardTitle>
      <CardDescription v-if="endpoints.data.value">
        {{ enabledCount }} enabled / {{ endpoints.data.value.length }}
      </CardDescription>
      <CardAction>
        <Button variant="ghost" size="sm" as-child>
          <NuxtLink to="/endpoints">View all <ArrowRight /></NuxtLink>
        </Button>
      </CardAction>
    </CardHeader>
    <CardContent>
      <Skeleton v-if="endpoints.isPending.value" class="h-32" />
      <QueryError v-else-if="endpoints.isError.value" :query="endpoints" class="text-sm" />
      <p v-else-if="endpoints.data.value?.length === 0" class="text-sm text-muted-foreground">
        No endpoints yet —
        <NuxtLink to="/endpoints" class="text-primary hover:underline">create one</NuxtLink>.
      </p>
      <ul v-else class="divide-y">
        <li
          v-for="endpoint in endpoints.data.value"
          :key="endpoint.id"
          :class="cn('space-y-1 py-2', { 'opacity-60': !endpoint.enabled })"
        >
          <NuxtLink
            :to="`/endpoints/${endpoint.id}`"
            class="block truncate font-mono text-xs hover:underline"
          >
            {{ endpoint.url }}
          </NuxtLink>
          <EventTypeChips :types="endpoint.event_types" />
        </li>
      </ul>
    </CardContent>
  </Card>
</template>
