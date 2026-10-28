<script setup lang="ts">
import { Toaster } from '@repo/ui'

const links = [
  { to: '/', label: 'Deliveries' },
  { to: '/endpoints', label: 'Endpoints' },
]
</script>

<template>
  <div class="min-h-screen">
    <header class="border-b bg-card">
      <nav class="mx-auto flex h-topbar max-w-content items-center gap-6 px-4">
        <span class="font-semibold">Benji Webhooks</span>
        <NuxtLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="text-sm text-muted-foreground hover:text-foreground"
          active-class="!text-foreground font-medium"
        >
          {{ link.label }}
        </NuxtLink>
        <ThemeToggle class="ml-auto" />
      </nav>
    </header>
    <main class="mx-auto max-w-content px-4 py-8">
      <NuxtPage />
    </main>
    <Toaster rich-colors />
  </div>
</template>
