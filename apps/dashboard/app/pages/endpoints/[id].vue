<script setup lang="ts">
import { ArrowLeft } from '@lucide/vue'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Label,
  PageHeader,
  Skeleton,
  Switch,
} from '@repo/ui'

const route = useRoute()
const id = computed(() => String(route.params.id))
const endpoint = useEndpoint(id)
const update = useUpdateEndpoint()
</script>

<template>
  <section class="space-y-6">
    <NuxtLink
      to="/endpoints"
      class="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
    >
      <ArrowLeft class="size-4" /> Endpoints
    </NuxtLink>

    <div v-if="endpoint.isPending.value" class="space-y-6" aria-busy="true">
      <div class="flex items-center justify-between gap-4">
        <div class="space-y-2">
          <Skeleton class="h-8 w-96 max-w-full" />
          <Skeleton class="h-4 w-64" />
        </div>
        <Skeleton class="h-5 w-24" />
      </div>
      <div class="grid gap-4 xl:grid-cols-2">
        <Skeleton class="h-56 rounded-card" />
        <Skeleton class="h-56 rounded-card" />
      </div>
      <Skeleton class="h-64 rounded-card" />
    </div>
    <Card v-else-if="endpoint.isError.value">
      <LoadError :message="endpoint.error.value?.message" @retry="endpoint.refetch()" />
    </Card>
    <template v-else-if="endpoint.data.value">
      <PageHeader>
        <template #title>
          <span class="font-mono">{{ endpoint.data.value.url }}</span>
        </template>
        <template #description>
          {{ endpoint.data.value.description || 'No description' }} ·
          <span class="font-mono">{{ endpoint.data.value.id }}</span>
        </template>
        <div class="flex items-center gap-2">
          <Label for="endpoint-enabled">
            {{ endpoint.data.value.enabled ? 'Enabled' : 'Paused' }}
          </Label>
          <Switch
            id="endpoint-enabled"
            :model-value="endpoint.data.value.enabled"
            :disabled="update.isPending.value"
            @update:model-value="(enabled) => update.mutate({ id, enabled })"
          />
        </div>
      </PageHeader>

      <div class="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Event types</CardTitle>
            <CardDescription>
              Pick what this endpoint receives. Only future events: deliveries already queued still
              go out.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <EventTypeSwitches :endpoint="endpoint.data.value" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Deliveries by status</CardTitle>
            <CardDescription>
              Pausing the endpoint stops every delivery to this URL; the URL and the secret stay.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DeliveryStatsSummary :endpoint-id="id" />
          </CardContent>
        </Card>
      </div>

      <DeliveriesTable :filters="{ endpointId: id }" :show-endpoint="false" />
    </template>
  </section>
</template>
