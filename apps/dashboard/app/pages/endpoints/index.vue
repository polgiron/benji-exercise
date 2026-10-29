<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { Button, PageHeader } from '@repo/ui'

const route = useRoute()
const router = useRouter()
// `/endpoints?create` (the overview's "New endpoint") opens the dialog straight away.
const creating = ref(route.query.create !== undefined)
if (creating.value) router.replace({ query: { ...route.query, create: undefined } })
</script>

<template>
  <section class="space-y-4">
    <PageHeader
      title="Endpoints"
      description="The URLs Benji signs and sends events to, and which events each one gets."
    >
      <Button @click="creating = true"><Plus /> New endpoint</Button>
    </PageHeader>
    <EndpointList @create="creating = true" />
    <CreateEndpointDialog v-model:open="creating" />
  </section>
</template>
