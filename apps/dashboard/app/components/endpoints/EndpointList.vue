<script setup lang="ts">
import {
  Button,
  Card,
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
          <TableRow v-for="n in 3" :key="n">
            <TableCell :colspan="3"><Skeleton class="h-5" /></TableCell>
          </TableRow>
        </template>
        <TableEmpty v-else-if="endpoints.isError.value" :colspan="3">
          <span class="text-destructive-foreground">{{ endpoints.error.value?.message }}</span>
        </TableEmpty>
        <TableEmpty v-else-if="endpoints.data.value?.length === 0" :colspan="3">
          <span class="text-muted-foreground">
            No endpoints yet —
            <Button variant="link" size="inline" @click="$emit('create')">create one</Button>
          </span>
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
