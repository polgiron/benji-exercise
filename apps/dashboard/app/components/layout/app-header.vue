<script setup lang="ts">
import {
  LayoutDashboard,
  PanelRightClose,
  PanelRightOpen,
  Send,
  ShieldCheck,
  Webhook,
} from '@lucide/vue'
import { BrandMark, Button, cn } from '@repo/ui'

const route = useRoute()
const testPanelOpen = useTestPanel()

const links = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/deliveries', label: 'Deliveries', icon: Send },
  { to: '/endpoints', label: 'Endpoints', icon: Webhook },
  { to: '/how-it-works', label: 'How it works', icon: ShieldCheck },
]

// `/endpoints/ep_…` keeps "Endpoints" lit; `/` only matches itself.
const isActive = (to: string) => (to === '/' ? route.path === '/' : route.path.startsWith(to))
</script>

<template>
  <header class="border-b bg-card">
    <nav class="flex h-16 items-stretch gap-8 px-6">
      <!-- The docs' lockup: the round mark, then the product name in brand purple. -->
      <NuxtLink to="/" class="flex items-center gap-2" aria-label="Benji Webhooks, overview">
        <BrandMark />
        <span class="text-xl font-semibold tracking-tight text-brand">Webhooks</span>
      </NuxtLink>
      <div class="flex items-stretch gap-6">
        <NuxtLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          :aria-current="isActive(link.to) ? 'page' : undefined"
          :class="
            cn(
              'relative flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground',
              'after:absolute after:inset-x-0 after:-bottom-px after:h-0.5 after:origin-center after:scale-x-0 after:rounded-full after:bg-primary after:transition-transform after:duration-300 after:ease-out-quart',
              { 'text-foreground after:scale-x-100': isActive(link.to) },
            )
          "
        >
          <component :is="link.icon" class="size-4" />
          {{ link.label }}
        </NuxtLink>
      </div>
      <div class="ml-auto flex items-center gap-4">
        <ConnectionStatus />
        <ThemeToggle />
        <Button
          variant="ghost"
          size="icon-sm"
          :aria-label="testPanelOpen ? 'Hide the test panel' : 'Show the test panel'"
          :title="testPanelOpen ? 'Hide the test panel' : 'Show the test panel'"
          :aria-pressed="testPanelOpen"
          @click="testPanelOpen = !testPanelOpen"
        >
          <PanelRightClose v-if="testPanelOpen" />
          <PanelRightOpen v-else />
        </Button>
      </div>
    </nav>
  </header>
</template>
