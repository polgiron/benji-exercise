<script setup lang="ts">
import { Check, Copy, TriangleAlert } from '@lucide/vue'
import { Button } from '@repo/ui'
import { useClipboard } from '@vueuse/core'

interface Props {
  secret: string
}

defineProps<Props>()
const { copy, copied } = useClipboard({ copiedDuring: 1500 })
</script>

<template>
  <div class="space-y-3">
    <div class="flex gap-2 rounded-md bg-warning/10 px-3 py-2 text-sm text-warning-foreground">
      <TriangleAlert class="mt-0.5 size-4 shrink-0" />
      <p>
        Copy the signing secret now: <strong>you won't see it again</strong>. The receiver uses it
        to verify each delivery's signature.
      </p>
    </div>
    <div class="flex items-center gap-2">
      <code class="min-w-0 flex-1 truncate rounded-md border bg-muted px-3 py-2 font-mono text-xs">
        {{ secret }}
      </code>
      <Button variant="outline" size="sm" @click="copy(secret)">
        <Check v-if="copied" />
        <Copy v-else />
        {{ copied ? 'Copied' : 'Copy' }}
      </Button>
    </div>
  </div>
</template>
