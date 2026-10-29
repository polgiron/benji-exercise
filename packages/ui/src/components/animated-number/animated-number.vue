<script setup lang="ts">
import { TransitionPresets, usePreferredReducedMotion, useTransition } from '@vueuse/core'
import { computed, onMounted, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    value: number
    /** Formats the in-between values too, so keep it cheap. Defaults to grouped integers. */
    format?: (value: number) => string
    duration?: number
  }>(),
  { format: (value: number) => Math.round(value).toLocaleString('en'), duration: 700 },
)

const reducedMotion = usePreferredReducedMotion()
// Starts at 0 and counts up once mounted; later changes tween from the current value.
const target = ref(0)
const shown = useTransition(target, {
  duration: computed(() => props.duration),
  easing: TransitionPresets.easeOutQuart,
  disabled: computed(() => reducedMotion.value === 'reduce'),
})

onMounted(() => (target.value = props.value))
watch(
  () => props.value,
  (value) => (target.value = value),
)

const text = computed(() => props.format(shown.value))
</script>

<template>
  <span data-slot="animated-number" class="tabular-nums">{{ text }}</span>
</template>
