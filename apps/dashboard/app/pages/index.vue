<script setup lang="ts">
import { PageHeader } from '@repo/ui'
</script>

<template>
  <section class="space-y-6">
    <PageHeader title="Overview" />
    <div class="grid gap-4 xl:grid-cols-2">
      <DeliveriesCard />
      <EndpointsCard />
    </div>
  </section>
</template>
