<script setup lang="ts">
import { Webhook } from '@lucide/vue'
import { IconTile, cn } from '@repo/ui'

const route = useRoute()

const links = [
  { to: '/', label: 'Overview' },
  { to: '/deliveries', label: 'Deliveries' },
  { to: '/endpoints', label: 'Endpoints' },
]

// `/endpoints/ep_…` keeps "Endpoints" lit; `/` only matches itself.
const isActive = (to: string) => (to === '/' ? route.path === '/' : route.path.startsWith(to))
</script>

<template>
  <header class="border-b bg-card">
    <nav class="flex h-14 items-center gap-6 px-6">
      <NuxtLink to="/" class="flex items-center gap-2 font-semibold">
        <IconTile><Webhook /></IconTile>
        Benji Webhooks
      </NuxtLink>
      <NuxtLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        :class="
          cn('text-sm text-muted-foreground hover:text-foreground', {
            'font-medium text-foreground': isActive(link.to),
          })
        "
      >
        {{ link.label }}
      </NuxtLink>
      <ThemeToggle class="ml-auto" />
    </nav>
  </header>
</template>
