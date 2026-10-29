<script setup lang="ts">
import { NuxtLink } from '#components'
import { AnimatedNumber, Card, IconTile, Skeleton, cn } from '@repo/ui'
import type { Component } from 'vue'

interface Props {
  label: string
  icon: Component
  /** Undefined while loading, or when there is nothing to show yet (see `loading`). */
  value?: number
  loading?: boolean
  format?: (value: number) => string
  hint?: string
  to?: string
  danger?: boolean
}

defineProps<Props>()
</script>

<template>
  <component :is="to ? NuxtLink : 'div'" :to="to" class="group block rounded-card">
    <Card
      class="relative h-full gap-0 overflow-hidden p-5 transition duration-300 ease-out-quart group-hover:-translate-y-0.5 group-hover:shadow-popover motion-reduce:transition-none"
    >
      <!-- The Pilot tiles' faint grid, fading out from behind the icon. -->
      <div
        aria-hidden="true"
        class="absolute inset-x-0 top-0 h-32 bg-grid mask-[radial-gradient(ellipse_at_top_left,black,transparent_65%)]"
      />
      <IconTile class="relative size-10 rounded-lg [&_svg]:size-5">
        <component :is="icon" />
      </IconTile>
      <div class="relative mt-7">
        <Skeleton v-if="loading" class="h-9 w-20" />
        <p
          v-else
          :class="
            cn('text-3xl font-semibold tracking-tight', {
              'text-destructive-foreground': danger,
            })
          "
        >
          <AnimatedNumber v-if="value !== undefined" :value="value" :format="format" />
          <span v-else class="text-muted-foreground">–</span>
        </p>
        <p class="mt-1 text-sm text-muted-foreground">{{ label }}</p>
        <p v-if="hint" class="mt-0.5 truncate text-xs text-muted-foreground/80">{{ hint }}</p>
      </div>
    </Card>
  </component>
</template>
