<script setup lang="ts">
import { LoaderCircle, RotateCw } from '@lucide/vue'
import { Button } from '@repo/ui'
import type { Ref } from 'vue'

interface Props {
  query: {
    error: Readonly<Ref<Error | null>>
    isFetching: Readonly<Ref<boolean>>
    refetch: () => Promise<unknown>
  }
}

defineProps<Props>()
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <span class="text-destructive-foreground">{{ query.error.value?.message }}</span>
    <Button
      variant="outline"
      size="xs"
      :disabled="query.isFetching.value"
      @click.stop="query.refetch()"
    >
      <LoaderCircle v-if="query.isFetching.value" class="animate-spin" />
      <RotateCw v-else />
      Retry
    </Button>
  </div>
</template>
