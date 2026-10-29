<script setup lang="ts">
import { Toaster } from '@repo/ui'

// Opened once for the whole app: every page reads the same live cache.
useDeliveryStream()
</script>

<template>
  <div class="flex h-screen flex-col">
    <AppHeader />
    <div class="flex min-h-0 flex-1 gap-4 p-4">
      <main class="min-w-0 flex-1 overflow-y-auto">
        <div class="mx-auto max-w-content px-2 py-4">
          <NuxtPage />
        </div>
      </main>
      <TestPanel class="w-96 shrink-0" />
    </div>
    <Toaster rich-colors />
  </div>
</template>
