<script setup lang="ts">
import { cn } from 'cn'
import type { HTMLAttributes } from 'vue'
import type { StatValueVariants } from '.'
import { statValueVariants } from '.'

const props = defineProps<{
  label: string
  value: number | string
  tone?: StatValueVariants['tone']
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <div data-slot="stat" :class="cn('rounded-input bg-muted px-3 py-2', props.class)">
    <dt class="text-2xs text-muted-foreground">{{ label }}</dt>
    <dd :class="statValueVariants({ tone })">{{ value }}</dd>
  </div>
</template>
