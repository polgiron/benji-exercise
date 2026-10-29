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

    <Skeleton v-if="endpoint.isPending.value" class="h-20" />
    <p v-else-if="endpoint.isError.value" class="text-destructive-foreground">
      {{ endpoint.error.value?.message }}
    </p>
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
