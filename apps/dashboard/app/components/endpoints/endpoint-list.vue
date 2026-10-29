<script setup lang="ts">
import { Plus, Webhook } from '@lucide/vue'
import {
  Button,
  Card,
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  Skeleton,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableEmpty,
  TableHead,
  TableHeader,
  TableRow,
  cn,
} from '@repo/ui'

defineEmits<{ create: [] }>()

const endpoints = useEndpoints()
const update = useUpdateEndpoint()

const isUpdating = (id: string) => update.isPending.value && update.variables.value?.id === id
</script>

<template>
  <Card class="gap-0 overflow-hidden py-0">
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>URL</TableHead>
          <TableHead>Event types</TableHead>
          <TableHead class="text-right">Enabled</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <template v-if="endpoints.isPending.value">
          <TableRow v-for="n in 4" :key="n" class="hover:bg-transparent" aria-busy="true">
            <TableCell class="space-y-1.5">
              <Skeleton class="h-3.5 w-64" />
              <Skeleton class="h-3 w-40" />
            </TableCell>
            <TableCell>
              <div class="flex gap-1">
                <Skeleton class="h-5 w-24" />
                <Skeleton class="h-5 w-28" />
              </div>
            </TableCell>
            <TableCell><Skeleton class="ml-auto h-5 w-9 rounded-full" /></TableCell>
          </TableRow>
        </template>
        <TableEmpty v-else-if="endpoints.isError.value" :colspan="3" class="whitespace-normal">
          <LoadError :message="endpoints.error.value?.message" @retry="endpoints.refetch()" />
        </TableEmpty>
        <TableEmpty
          v-else-if="endpoints.data.value?.length === 0"
          :colspan="3"
          class="whitespace-normal"
        >
          <Empty class="p-4 md:p-8">
            <EmptyHeader>
              <EmptyMedia variant="glow"><Webhook /></EmptyMedia>
              <EmptyTitle class="text-base">No endpoints yet</EmptyTitle>
              <EmptyDescription>
                An endpoint is a URL of yours that Benji signs and sends events to. Add one, pick
                its event types, and you're live.
              </EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
              <Button size="sm" @click="$emit('create')"><Plus /> New endpoint</Button>
            </EmptyContent>
          </Empty>
        </TableEmpty>
        <TableRow
          v-for="endpoint in endpoints.data.value"
          v-else
          :key="endpoint.id"
          :class="cn({ 'opacity-60': !endpoint.enabled })"
        >
          <TableCell class="max-w-96">
            <NuxtLink
              :to="`/endpoints/${endpoint.id}`"
              class="block truncate font-mono text-xs hover:underline"
            >
              {{ endpoint.url }}
            </NuxtLink>
            <p v-if="endpoint.description" class="truncate text-xs text-muted-foreground">
              {{ endpoint.description }}
            </p>
          </TableCell>
          <TableCell class="whitespace-normal">
            <EventTypeChips :types="endpoint.event_types" />
          </TableCell>
          <TableCell class="text-right">
            <Switch
              :model-value="endpoint.enabled"
              :disabled="isUpdating(endpoint.id)"
              :aria-label="`Enable ${endpoint.url}`"
              @update:model-value="(enabled) => update.mutate({ id: endpoint.id, enabled })"
            />
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </Card>
</template>
