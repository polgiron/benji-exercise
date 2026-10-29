<script setup lang="ts">
import { cn } from 'cn'
import type { HTMLAttributes } from 'vue'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <!-- Benji's round "b" mark, from the docs logo. Brand colors in both themes, on purpose. -->
  <svg
    data-slot="brand-mark"
    viewBox="0 0 220 220"
    aria-hidden="true"
    :class="cn('size-7 shrink-0', props.class)"
  >
    <circle cx="110" cy="110" r="108.1" class="fill-brand" />
    <path
      class="fill-brand-foreground"
      d="M119.5,77c-15.9,0-27.5,4.1-35.3,10.9-1.6,1.3-2.7,2.8-4.1,4.2v-43.3h-35.9v122.4h35.8v-15.1c1.4,1.4,2.5,2.9,4.1,4.2,7.8,6.8,19.4,10.9,35.3,10.9,31,0,56.6-20.5,56.7-47.1,0-26.6-25.6-47.1-56.6-47.1ZM123.1,141.4c-20.1,7.7-39.6,5.8-42.6-4.1,0-.3-.2-.7-.3-1.1-.3-2-.1-4.1.7-6.1l.3-.7c1.6-3.5,8.2-16.1,30.9-24.5,8.7-3.2,17.7-5,26.5-4.6h.8c3.8.2,7.3,1.2,10.4,2.9l.5.3c1.7,1.1,3.1,2.5,3.9,4.3.2.3.4.7.4,1.3,3,9.8-11.4,24.7-31.5,32.3Z"
    />
  </svg>
</template>
