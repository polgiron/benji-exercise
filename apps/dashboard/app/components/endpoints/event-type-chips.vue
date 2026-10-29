<script setup lang="ts">
interface Props {
  types: string[]
}

defineProps<Props>()
</script>

<template>
  <div class="flex flex-wrap gap-1">
    <EventTypeBadge v-for="type in types" :key="type" :type="type" />
  </div>
</template>
