<script setup lang="ts">
import { DatabaseZap, LoaderCircle } from '@lucide/vue'
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
const seed = useSeedDemo()

function confirm() {
  seed.mutate(undefined, {
    onSuccess: () => {
      open.value = false
      // The page open may show an endpoint that is gone; the overview shows the new data.
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
    <Button variant="outline" size="sm" class="w-fit" @click="open = true">
      <DatabaseZap />
      Reset and seed…
    </Button>

    <Dialog v-model:open="open">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Reset and seed the database?</DialogTitle>
          <DialogDescription>
            Every endpoint, event and delivery is deleted first, the ones you created included.
            There is no undo.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="open = false">Cancel</Button>
          <Button variant="destructive" :disabled="seed.isPending.value" @click="confirm">
            <LoaderCircle v-if="seed.isPending.value" class="animate-spin" />
            Delete and seed
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </Card>
</template>
