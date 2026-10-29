<script setup lang="ts">
import { LoaderCircle } from '@lucide/vue'
import {
  Button,
  Checkbox,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Input,
  Label,
} from '@repo/ui'
import { type IMockReceiver, MOCK_RECEIVERS, mockReceiverUrl } from '~/api/mock'

const open = defineModel<boolean>('open', { required: true })

const eventTypes = useEventTypes()
const create = useCreateEndpoint()

const url = ref('')
const description = ref('')
const selected = ref<string[]>([])
// Lives here only: never in the query cache, gone when the dialog closes.
const secret = ref<string>()

function toggleType(key: string, checked: boolean) {
  selected.value = checked ? [...selected.value, key] : selected.value.filter((k) => k !== key)
}

// The API refuses a second endpoint on a URL (409); this says so before the submit.
const endpoints = useEndpoints()
const usedUrls = computed(() => new Map(endpoints.data.value?.map((e) => [e.url, e])))
const taken = computed(() => usedUrls.value.get(url.value.trim()))

const MOCK_DESCRIPTIONS = new Set(MOCK_RECEIVERS.map((receiver) => receiver.does))

function pickMock(receiver: IMockReceiver) {
  url.value = mockReceiverUrl(receiver.path)
  // Describe it too, unless the reviewer wrote their own: a list of mocks reads better labelled.
  if (!description.value || MOCK_DESCRIPTIONS.has(description.value)) {
    description.value = receiver.does
  }
}

function submit() {
  create.mutate(
    {
      url: url.value.trim(),
      description: description.value.trim() || null,
      event_types: selected.value,
    },
    {
      onSuccess: (endpoint) => {
        secret.value = endpoint.secret
        create.reset()
      },
    },
  )
}

watch(open, (isOpen) => {
  if (isOpen) return
  url.value = description.value = ''
  selected.value = []
  secret.value = undefined
  create.reset()
})
</script>

<template>
  <Dialog v-model:open="open">
    <DialogContent>
      <template v-if="secret">
        <DialogHeader>
          <DialogTitle>Endpoint created</DialogTitle>
          <DialogDescription>Deliveries start with the next matching event.</DialogDescription>
        </DialogHeader>
        <SecretReveal :secret="secret" />
        <DialogFooter>
          <Button @click="open = false">Done</Button>
        </DialogFooter>
      </template>

      <form v-else class="grid gap-4" @submit.prevent="submit">
        <DialogHeader>
          <DialogTitle>New endpoint</DialogTitle>
          <DialogDescription>
            Where to send webhooks, and for which event types. A mock receiver URL from the test
            panel works here.
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-1.5">
          <Label for="endpoint-url">URL</Label>
          <Input
            id="endpoint-url"
            v-model="url"
            type="url"
            required
            placeholder="https://example.com/webhooks"
            class="font-mono"
            :aria-invalid="!!taken"
            :aria-describedby="taken ? 'endpoint-url-taken' : undefined"
          />
          <p v-if="taken" id="endpoint-url-taken" class="text-xs text-destructive-foreground">
            Already used by {{ taken.description || taken.id }}: one endpoint per URL.
          </p>
          <div class="flex flex-wrap items-center gap-1 pt-1">
            <span class="mr-1 text-xs text-muted-foreground">Or a mock receiver:</span>
            <Button
              v-for="receiver in MOCK_RECEIVERS"
              :key="receiver.path"
              type="button"
              size="xs"
              :variant="url === mockReceiverUrl(receiver.path) ? 'secondary' : 'outline'"
              :aria-pressed="url === mockReceiverUrl(receiver.path)"
              :disabled="usedUrls.has(mockReceiverUrl(receiver.path))"
              :title="
                usedUrls.has(mockReceiverUrl(receiver.path))
                  ? 'Already used by an endpoint'
                  : `${receiver.answer} · ${receiver.does}`
              "
              class="font-mono"
              @click="pickMock(receiver)"
            >
              /mock/{{ receiver.path }}
            </Button>
          </div>
        </div>
        <div class="space-y-1.5">
          <Label for="endpoint-description"
            >Description <span class="text-muted-foreground">(optional)</span></Label
          >
          <Input id="endpoint-description" v-model="description" maxlength="500" />
        </div>
        <fieldset class="space-y-2">
          <legend class="mb-2 text-sm font-medium">Event types</legend>
          <LoadError
            v-if="eventTypes.isError.value"
            :message="eventTypes.error.value?.message"
            @retry="eventTypes.refetch()"
          />
          <template v-else>
            <div
              v-for="type in eventTypes.data.value"
              :key="type.key"
              class="flex items-start gap-2"
            >
              <Checkbox
                :id="`endpoint-type-${type.key}`"
                :model-value="selected.includes(type.key)"
                class="mt-0.5"
                @update:model-value="(checked) => toggleType(type.key, checked === true)"
              />
              <Label :for="`endpoint-type-${type.key}`" class="grid gap-1 font-normal">
                <EventTypeBadge :type="type.key" />
                <span class="text-xs text-muted-foreground">{{ type.description }}</span>
              </Label>
            </div>
          </template>
        </fieldset>
        <DialogFooter>
          <Button variant="outline" type="button" @click="open = false">Cancel</Button>
          <Button
            type="submit"
            :disabled="selected.length === 0 || !!taken || create.isPending.value"
          >
            <LoaderCircle v-if="create.isPending.value" class="animate-spin" />
            Create endpoint
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
