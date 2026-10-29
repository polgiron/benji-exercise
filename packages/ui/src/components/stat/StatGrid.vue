<script setup lang="ts">
import { cn } from 'cn'
import type { HTMLAttributes } from 'vue'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <!-- As many tiles per row as fit at `--spacing-stat` each: wraps in a narrow card. -->
  <dl data-slot="stat-grid" :class="cn('grid grid-cols-stats gap-2', props.class)">
    <slot />
  </dl>
</template>
