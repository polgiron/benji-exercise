<script setup lang="ts">
import { CodeBlock, Skeleton } from '@repo/ui'
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
      <Skeleton v-if="detail.isPending.value" class="h-32" />
      <CodeBlock v-else-if="detail.data.value" size="sm" height="md">{{
        JSON.stringify(detail.data.value.payload, null, 2)
      }}</CodeBlock>
    </div>
    <div class="min-w-0 space-y-1.5">
      <h4 class="text-xs font-medium text-muted-foreground">
        Attempts · <span class="font-mono">{{ delivery.id }}</span>
      </h4>
      <Skeleton v-if="detail.isPending.value" class="h-32" />
      <p v-else-if="detail.isError.value" class="text-xs text-destructive-foreground">
        {{ detail.error.value?.message }}
      </p>
      <AttemptLog v-else-if="detail.data.value" :attempts="detail.data.value.attempts" />
    </div>
  </div>
</template>
