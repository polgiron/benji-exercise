<script setup lang="ts">
import { cn } from 'cn'
import type { HTMLAttributes } from 'vue'

interface SkeletonProps {
  class?: HTMLAttributes['class']
}

const props = defineProps<SkeletonProps>()
</script>

<template>
  <!-- A sheen sweeps across instead of a pulse; reduced motion keeps the still shape. -->
  <div
    data-slot="skeleton"
    aria-hidden="true"
    :class="
      cn(
        'relative overflow-hidden rounded-md bg-foreground/6 before:absolute before:inset-0 before:-translate-x-full before:animate-shimmer before:bg-linear-to-r before:from-transparent before:via-foreground/6 before:to-transparent motion-reduce:before:hidden',
        props.class,
      )
    "
  />
</template>
