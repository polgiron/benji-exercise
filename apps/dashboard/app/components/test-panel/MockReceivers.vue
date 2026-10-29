<script setup lang="ts">
import { Check, Copy } from '@lucide/vue'
import { Button } from '@repo/ui'
import { useClipboard } from '@vueuse/core'
import { mockReceiverUrl } from '~/api/mock'

const RECEIVERS = [
  { path: 'ok', answer: '200', does: 'Accepts every delivery.' },
  { path: 'flaky?fail=2', answer: '503 ×2, then 200', does: 'Succeeds on the 3rd attempt.' },
  { path: 'fail', answer: '500', does: 'Retried until attempts run out, then failed.' },
  { path: 'reject', answer: '400', does: 'Terminal: failed at once, no retry.' },
  { path: 'slow?seconds=15', answer: 'after 15 s', does: 'Times out (10 s) and is retried.' },
]

const { copy, copied, text } = useClipboard({ copiedDuring: 1500 })
</script>

<template>
  <section class="space-y-2">
    <div>
      <h3 class="text-sm font-medium">Mock receivers</h3>
      <p class="text-xs text-muted-foreground">
        Customer servers that check the signature, then answer as below. Paste one into a new
        endpoint.
      </p>
    </div>
    <ul class="divide-y rounded-md border">
      <li
        v-for="receiver in RECEIVERS"
        :key="receiver.path"
        class="flex items-start gap-2 px-3 py-2"
      >
        <div class="min-w-0 flex-1">
          <p class="truncate font-mono text-2xs">/mock/{{ receiver.path }}</p>
          <p class="text-xs text-muted-foreground">
            <span class="font-medium text-foreground">{{ receiver.answer }}</span> ·
            {{ receiver.does }}
          </p>
        </div>
        <Button
          variant="ghost"
          size="icon-xs"
          :aria-label="`Copy /mock/${receiver.path}`"
          @click="copy(mockReceiverUrl(receiver.path))"
        >
          <Check v-if="copied && text === mockReceiverUrl(receiver.path)" />
          <Copy v-else />
        </Button>
      </li>
    </ul>
  </section>
</template>
