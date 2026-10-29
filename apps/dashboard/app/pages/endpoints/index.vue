<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { Button, PageHeader } from '@repo/ui'

const creating = ref(false)
</script>

<template>
  <section class="space-y-4">
    <PageHeader title="Endpoints">
      <Button @click="creating = true"><Plus /> New endpoint</Button>
    </PageHeader>
    <EndpointList @create="creating = true" />
    <CreateEndpointDialog v-model:open="creating" />
  </section>
</template>
