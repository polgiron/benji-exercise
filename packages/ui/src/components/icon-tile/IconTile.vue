<script setup lang="ts">
import { cn } from 'cn'
import type { HTMLAttributes } from 'vue'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <!-- An icon on the lavender accent tint (the logo mark, feature icons). -->
  <span
    data-slot="icon-tile"
    :class="
      cn(
        'grid size-7 shrink-0 place-items-center rounded-button bg-accent text-accent-foreground [&_svg]:size-4',
        props.class,
      )
    "
  >
    <slot />
  </span>
</template>
