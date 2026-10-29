<script setup lang="ts">
import { Toaster } from '@repo/ui'

// Opened once for the whole app: every page reads the same live cache.
useDeliveryStream()
const testPanelOpen = useTestPanel()
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
      <Transition
        enter-from-class="opacity-0 translate-x-4"
        leave-to-class="opacity-0 translate-x-4"
        enter-active-class="transition duration-300 ease-out-quart motion-reduce:transition-none"
        leave-active-class="transition duration-200 ease-out-quart motion-reduce:transition-none"
      >
        <TestPanel v-if="testPanelOpen" class="w-96 shrink-0" />
      </Transition>
    </div>
    <Toaster rich-colors />
  </div>
</template>
