<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { getHealth } from '~/api/health'

const health = useQuery({ queryKey: ['health'], queryFn: getHealth })
</script>

<template>
  <section class="space-y-2">
    <h1 class="text-2xl font-semibold">Deliveries</h1>
    <p class="text-sm text-muted-foreground">
      API:
      <span v-if="health.isPending.value">checking…</span>
      <span v-else-if="health.isError.value" class="text-destructive">{{ health.error.value?.message }}</span>
      <span v-else>{{ health.data.value?.status }}</span>
    </p>
  </section>
</template>
