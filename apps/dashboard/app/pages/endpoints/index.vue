<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { Button } from '@repo/ui'

const creating = ref(false)
</script>

<template>
  <section class="space-y-4">
    <div class="flex items-center gap-3">
      <h1 class="mr-auto text-2xl font-semibold">Endpoints</h1>
      <Button @click="creating = true"><Plus /> New endpoint</Button>
    </div>
    <EndpointList @create="creating = true" />
    <CreateEndpointDialog v-model:open="creating" />
  </section>
</template>
