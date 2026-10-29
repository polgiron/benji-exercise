<script setup lang="ts">
import { cn } from 'cn'
import type { HTMLAttributes } from 'vue'
import type { StatusDotVariants } from '.'
import { statusDotVariants } from '.'

const props = defineProps<{
  tone?: StatusDotVariants['tone']
  pulse?: boolean
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <span
    data-slot="status-dot"
    aria-hidden="true"
    :class="cn(statusDotVariants({ tone, pulse }), props.class)"
  />
</template>
