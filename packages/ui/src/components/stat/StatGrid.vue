<script setup lang="ts">
import { cn } from 'cn'
import type { HTMLAttributes } from 'vue'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <!-- Columns follow the space the grid gets (a container query), not the viewport: it sits
       in half-width cards as well as full-width ones. -->
  <div class="@container">
    <dl
      data-slot="stat-grid"
      :class="cn('grid grid-cols-2 gap-2 @xs:grid-cols-3 @lg:grid-cols-5', props.class)"
    >
      <slot />
    </dl>
  </div>
</template>
