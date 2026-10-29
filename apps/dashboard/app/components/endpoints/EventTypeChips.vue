<script setup lang="ts">
import { Badge } from '@repo/ui'

interface Props {
  types: string[]
}

defineProps<Props>()
</script>

<template>
  <div class="flex flex-wrap gap-1">
    <Badge v-for="type in types" :key="type" variant="secondary" class="font-mono text-2xs">
      {{ type }}
    </Badge>
  </div>
</template>
