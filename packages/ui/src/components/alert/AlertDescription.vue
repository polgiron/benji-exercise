<script setup lang="ts">
import { cn } from 'cn'
import type { HTMLAttributes } from 'vue'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <div
    data-slot="alert-description"
    :class="
      cn('col-start-2 grid justify-items-start gap-1 text-sm break-words opacity-90', props.class)
    "
  >
    <slot />
  </div>
</template>
