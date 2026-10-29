<script setup lang="ts">
import { cn } from 'cn'
import type { HTMLAttributes } from 'vue'

const props = defineProps<{
  title?: string
  description?: string
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <!-- A page's h1, with its actions (filters, a create button) on the right. -->
  <header data-slot="page-header" :class="cn('flex flex-wrap items-center gap-3', props.class)">
    <div class="mr-auto min-w-0">
      <h1 class="truncate text-2xl font-semibold">
        <slot name="title">{{ title }}</slot>
      </h1>
      <p v-if="description || $slots.description" class="text-sm text-muted-foreground">
        <slot name="description">{{ description }}</slot>
      </p>
    </div>
    <slot />
  </header>
</template>
