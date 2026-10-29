<script setup lang="ts">
import { Check, Copy, TriangleAlert } from '@lucide/vue'
import { Alert, AlertDescription, Button, CodeBlock } from '@repo/ui'
import { useClipboard } from '@vueuse/core'

interface Props {
  secret: string
}

defineProps<Props>()
const { copy, copied } = useClipboard({ copiedDuring: 1500 })
</script>

<template>
  <div class="space-y-3">
    <Alert variant="warning">
      <TriangleAlert />
      <AlertDescription>
        <p>
          Copy the signing secret now: <strong>you won't see it again</strong>. The receiver uses it
          to verify each delivery's signature.
        </p>
      </AlertDescription>
    </Alert>
    <div class="flex items-center gap-2">
      <CodeBlock surface="muted" size="line" class="min-w-0 flex-1">{{ secret }}</CodeBlock>
      <Button variant="outline" size="sm" @click="copy(secret)">
        <Check v-if="copied" />
        <Copy v-else />
        {{ copied ? 'Copied' : 'Copy' }}
      </Button>
    </div>
  </div>
</template>
