<script setup lang="ts">
import { CodeBlock, Skeleton, cn } from '@repo/ui'
import type { IDeliverySummary } from '~/api/types'

interface Props {
  delivery: IDeliverySummary
}

const props = defineProps<Props>()
const detail = useDelivery(() => props.delivery.id)
</script>

<template>
  <div class="grid gap-4 p-4 lg:grid-cols-2">
    <div class="min-w-0 space-y-1.5">
      <h4 class="text-xs font-medium text-muted-foreground">
        Payload · <span class="font-mono">{{ delivery.event_id }}</span>
      </h4>
      <div v-if="detail.isPending.value" class="space-y-2 rounded-md border bg-card p-3">
        <!-- Ragged widths, like the lines of a JSON payload. -->
        <Skeleton
          v-for="(width, index) in ['w-8', 'w-40', 'w-56', 'w-32', 'w-48', 'w-8']"
          :key="index"
          :class="cn('h-3', width)"
        />
      </div>
      <CodeBlock v-else-if="detail.data.value" size="sm" height="md">{{
        JSON.stringify(detail.data.value.payload, null, 2)
      }}</CodeBlock>
    </div>
    <div class="min-w-0 space-y-1.5">
      <h4 class="text-xs font-medium text-muted-foreground">
        Attempts · <span class="font-mono">{{ delivery.id }}</span>
      </h4>
      <ul v-if="detail.isPending.value" class="space-y-2">
        <li v-for="n in 3" :key="n" class="flex items-center gap-3 rounded-md border bg-card p-3">
          <Skeleton class="size-6 rounded-full" />
          <Skeleton class="h-3 w-24" />
          <Skeleton class="ml-auto h-3 w-16" />
        </li>
      </ul>
      <LoadError
        v-else-if="detail.isError.value"
        :message="detail.error.value?.message"
        @retry="detail.refetch()"
      />
      <AttemptLog v-else-if="detail.data.value" :attempts="detail.data.value.attempts" />
    </div>
  </div>
</template>
