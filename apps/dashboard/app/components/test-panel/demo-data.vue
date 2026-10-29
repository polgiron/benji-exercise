<script lang="ts">
enum EDemoAction {
  SEED = 'seed',
  RESET = 'reset',
}

const COPY = {
  [EDemoAction.SEED]: {
    title: 'Reset and seed the database?',
    description:
      'Every endpoint, event and delivery is deleted first, the ones you created included. There is no undo.',
    confirm: 'Delete and seed',
  },
  [EDemoAction.RESET]: {
    title: 'Reset the database?',
    description:
      'Every endpoint, event and delivery is deleted, the ones you created included. Only the event types stay. There is no undo.',
    confirm: 'Delete everything',
  },
}
</script>

<script setup lang="ts">
import { DatabaseZap, LoaderCircle, Trash2 } from '@lucide/vue'
import {
  Button,
  Card,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@repo/ui'

const open = ref(false)
// Kept apart from `open` so the dialog's copy doesn't change while it fades out.
const action = ref(EDemoAction.SEED)
const seed = useSeedDemo()
const reset = useResetDemo()
const mutation = computed(() => (action.value === EDemoAction.SEED ? seed : reset))

function ask(next: EDemoAction) {
  action.value = next
  open.value = true
}

function confirm() {
  mutation.value.mutate(undefined, {
    onSuccess: () => {
      open.value = false
      // The page open may show an endpoint that is gone; the overview reflects the new state.
      return navigateTo('/')
    },
  })
}
</script>

<template>
  <Card class="gap-3 p-4">
    <div>
      <h3 class="text-sm font-medium">Demo data</h3>
      <p class="text-xs text-muted-foreground">
        Endpoints on the mock receivers and a month of their deliveries, so every page has something
        to show. A few live events follow, for the worker to retry as you watch.
      </p>
    </div>
    <div class="flex flex-wrap gap-2">
      <Button variant="ghost" size="sm" @click="ask(EDemoAction.RESET)">
        <Trash2 />
        Reset
      </Button>
      <Button variant="outline" size="sm" @click="ask(EDemoAction.SEED)">
        <DatabaseZap />
        Seed
      </Button>
    </div>

    <Dialog v-model:open="open">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{{ COPY[action].title }}</DialogTitle>
          <DialogDescription>{{ COPY[action].description }}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="open = false">Cancel</Button>
          <Button variant="destructive" :disabled="mutation.isPending.value" @click="confirm">
            <LoaderCircle v-if="mutation.isPending.value" class="animate-spin" />
            {{ COPY[action].confirm }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </Card>
</template>
