<script setup lang="ts">
import { Toaster } from '@/components/ui/sonner'
import 'vue-sonner/style.css'

const links = [
  { to: '/', label: 'Deliveries' },
  { to: '/endpoints', label: 'Endpoints' },
]
</script>

<template>
  <div class="min-h-screen">
    <header class="border-b">
      <nav class="mx-auto flex h-14 max-w-6xl items-center gap-6 px-4">
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
      </nav>
    </header>
    <main class="mx-auto max-w-6xl px-4 py-8">
      <NuxtPage />
    </main>
    <Toaster rich-colors />
  </div>
</template>
