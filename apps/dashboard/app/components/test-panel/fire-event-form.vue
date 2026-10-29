<script setup lang="ts">
import { LoaderCircle, RefreshCw, Repeat, Send } from '@lucide/vue'
import {
  Button,
  CodeBlock,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
} from '@repo/ui'
import { ApiError } from '~/api/client'

const eventTypes = useEventTypes()
const form = useFireEvent()
const showSchema = ref(false)

const selected = computed(() => eventTypes.data.value?.find((t) => t.key === form.eventType.value))

// Pick the first type once the catalogue is in, and prefill each type with its sample.
watch(
  () => eventTypes.data.value,
  (types) => {
    if (types?.length && !form.eventType.value) form.eventType.value = types[0]!.key
  },
  { immediate: true },
)
// Immediate: with the catalogue already cached, `selected` is set before this watcher exists
// (the panel re-opened), so it would never see a change and the payload would stay empty.
watch(
  selected,
  (type) => {
    if (type) form.payloadText.value = JSON.stringify(type.sample_payload, null, 2)
  },
  { immediate: true },
)

const error = computed(() => {
  const value = form.mutation.error.value
  return value instanceof ApiError ? value : null
})
// Which button spins: a re-submit sends the last request again, with its key.
const isResubmit = computed(
  () => form.mutation.variables.value?.idempotencyKey === form.lastSent.value?.idempotencyKey,
)
</script>

<template>
  <section class="space-y-3">
    <div>
      <h3 class="text-sm font-medium">Fire event</h3>
      <p class="text-xs text-muted-foreground">
        What Benji's services would send: it fans out to every endpoint subscribed to the type.
      </p>
    </div>

    <!-- Without the catalogue there is nothing to pick or prefill: the form waits for it. -->
    <LoadError
      v-if="eventTypes.isError.value"
      :message="eventTypes.error.value?.message"
      @retry="eventTypes.refetch()"
    />
    <template v-else>
      <div class="space-y-1.5">
        <Label for="fire-type">Event type</Label>
        <Select v-model="form.eventType.value" :disabled="eventTypes.isPending.value">
          <SelectTrigger id="fire-type" class="w-full">
            <SelectValue placeholder="Loading types…" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="type in eventTypes.data.value" :key="type.key" :value="type.key">
              <EventTypeBadge :type="type.key" />
            </SelectItem>
          </SelectContent>
        </Select>
        <p v-if="selected" class="text-xs text-muted-foreground">{{ selected.description }}</p>
      </div>

      <div class="space-y-1.5">
        <div class="flex items-center justify-between">
          <Label for="fire-payload">Payload</Label>
          <Button v-if="selected" variant="link" size="inline" @click="showSchema = !showSchema">
            {{ showSchema ? 'Hide schema' : 'Show schema' }}
          </Button>
        </div>
        <CodeBlock v-if="showSchema && selected" surface="muted" size="sm" height="sm">{{
          JSON.stringify(selected.payload_schema, null, 2)
        }}</CodeBlock>
        <Textarea
          id="fire-payload"
          v-model="form.payloadText.value"
          rows="9"
          spellcheck="false"
          class="font-mono text-xs"
        />
      </div>

      <div class="space-y-1.5">
        <Label for="fire-key">Idempotency key</Label>
        <div class="flex gap-1">
          <Input id="fire-key" v-model="form.idempotencyKey.value" class="font-mono text-xs" />
          <Button
            variant="outline"
            size="icon"
            aria-label="New idempotency key"
            @click="form.regenerateKey()"
          >
            <RefreshCw />
          </Button>
        </div>
        <p class="text-xs text-muted-foreground">
          One per intended action: a new key when the type or payload changes and after each send.
        </p>
      </div>

      <div class="flex flex-wrap gap-2">
        <Button
          :disabled="!form.eventType.value || form.mutation.isPending.value"
          @click="form.send()"
        >
          <LoaderCircle v-if="form.mutation.isPending.value && !isResubmit" class="animate-spin" />
          <Send v-else />
          Send event
        </Button>
        <Button
          variant="outline"
          :disabled="!form.lastSent.value || form.mutation.isPending.value"
          :title="form.lastSent.value ? `Key ${form.lastSent.value.idempotencyKey}` : undefined"
          @click="form.resubmit()"
        >
          <LoaderCircle v-if="form.mutation.isPending.value && isResubmit" class="animate-spin" />
          <Repeat v-else />
          Re-submit same key
        </Button>
      </div>

      <FireEventResult
        :parse-error="form.parseError.value"
        :error="error"
        :result="form.mutation.data.value"
      />
    </template>
  </section>
</template>
