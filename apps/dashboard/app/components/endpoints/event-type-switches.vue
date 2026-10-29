<script setup lang="ts">
import { Skeleton, Switch } from '@repo/ui'
import type { IEndpoint } from '~/api/types'

interface Props {
  endpoint: IEndpoint
}

const props = defineProps<Props>()
const eventTypes = useEventTypes()
const update = useUpdateEndpoint()

const isSubscribed = (key: string) => props.endpoint.event_types.includes(key)
// The API keeps at least one type per endpoint: pausing the endpoint is the way to stop all.
const isLast = (key: string) => isSubscribed(key) && props.endpoint.event_types.length === 1

function toggle(key: string, subscribed: boolean) {
  const types = eventTypes.data.value ?? []
  const next = types.map((t) => t.key).filter((k) => (k === key ? subscribed : isSubscribed(k)))
  update.mutate({ id: props.endpoint.id, event_types: next })
}
</script>

<template>
  <ul v-if="eventTypes.isPending.value" class="divide-y" aria-busy="true">
    <li v-for="n in 4" :key="n" class="flex items-center gap-4 py-3 first:pt-0 last:pb-0">
      <div class="flex-1 space-y-1.5">
        <Skeleton class="h-5 w-44" />
        <Skeleton class="h-3 w-64" />
      </div>
      <Skeleton class="h-5 w-9 rounded-full" />
    </li>
  </ul>
  <ul v-else class="divide-y">
    <li
      v-for="type in eventTypes.data.value"
      :key="type.key"
      class="flex items-center gap-4 py-3 first:pt-0 last:pb-0"
    >
      <div class="min-w-0 flex-1 space-y-1">
        <EventTypeBadge :type="type.key" />
        <p class="text-xs text-muted-foreground">
          {{ type.description }}
          <template v-if="isLast(type.key)">
            · The last type can't be removed: pause the endpoint instead.
          </template>
        </p>
      </div>
      <Switch
        :model-value="isSubscribed(type.key)"
        :disabled="update.isPending.value || isLast(type.key)"
        :aria-label="`Subscribe to ${type.key}`"
        @update:model-value="(subscribed) => toggle(type.key, subscribed)"
      />
    </li>
  </ul>
</template>
