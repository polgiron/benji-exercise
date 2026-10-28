<script setup lang="ts">
import { Moon, Sun } from '@lucide/vue'
import { Button } from '@repo/ui'
import { useColorMode } from '@vueuse/core'

// Follows the OS until the user picks; the choice is kept in localStorage.
const { store, state } = useColorMode()

function toggle() {
  store.value = state.value === 'dark' ? 'light' : 'dark'
}
</script>

<template>
  <Button variant="ghost" size="icon-sm" aria-label="Toggle theme" @click="toggle">
    <Sun v-if="state === 'dark'" />
    <Moon v-else />
  </Button>
</template>
