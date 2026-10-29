<script setup lang="ts">
import { FlaskConical } from '@lucide/vue'
import { Card, IconTile } from '@repo/ui'
</script>

<template>
  <Card class="min-h-0 gap-0 border-dashed py-0">
    <div class="flex items-start gap-3 border-b px-5 py-4">
      <IconTile><FlaskConical /></IconTile>
      <div>
        <h2 class="font-semibold">Test panel</h2>
        <p class="text-xs text-muted-foreground">
          Exercise tools, not part of the customer dashboard: in production Benji fires events and
          customers only receive them.
        </p>
      </div>
    </div>
    <div class="flex-1 space-y-6 overflow-y-auto px-5 py-4">
      <FireEventForm />
      <MockReceivers />
    </div>
  </Card>
</template>
