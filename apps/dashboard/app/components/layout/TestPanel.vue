<script setup lang="ts">
import { Card } from '@repo/ui'
</script>

<template>
  <Card class="min-h-0 gap-0 py-0">
    <div class="border-b px-5 py-4">
      <h2 class="font-semibold">Test panel</h2>
      <p class="text-xs text-muted-foreground">
        Exercise tools, not part of the customer dashboard: in production Benji fires events and
        customers only receive them.
      </p>
    </div>
    <div class="flex-1 space-y-6 overflow-y-auto px-5 py-4">
      <FireEventForm />
      <MockReceivers />
    </div>
    <div class="border-t px-5 py-3">
      <ConnectionStatus />
    </div>
  </Card>
</template>
