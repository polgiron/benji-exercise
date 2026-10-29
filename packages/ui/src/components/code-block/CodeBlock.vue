<script setup lang="ts">
import { cn } from 'cn'
import type { HTMLAttributes } from 'vue'
import type { CodeBlockVariants } from '.'
import { codeBlockVariants } from '.'

const props = defineProps<{
  surface?: CodeBlockVariants['surface']
  size?: CodeBlockVariants['size']
  height?: CodeBlockVariants['height']
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <pre
    data-slot="code-block"
    :class="cn(codeBlockVariants({ surface, size, height }), props.class)"
  ><slot /></pre>
</template>
