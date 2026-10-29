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
          />
        </div>
        <div class="space-y-1.5">
          <Label for="endpoint-description"
            >Description <span class="text-muted-foreground">(optional)</span></Label
          >
          <Input id="endpoint-description" v-model="description" maxlength="500" />
        </div>
        <fieldset class="space-y-2">
          <legend class="mb-2 text-sm font-medium">Event types</legend>
          <div v-for="type in eventTypes.data.value" :key="type.key" class="flex items-start gap-2">
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
        </fieldset>
        <DialogFooter>
          <Button variant="outline" type="button" @click="open = false">Cancel</Button>
          <Button type="submit" :disabled="selected.length === 0 || create.isPending.value">
            <LoaderCircle v-if="create.isPending.value" class="animate-spin" />
            Create endpoint
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
