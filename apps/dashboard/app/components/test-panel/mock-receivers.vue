<script setup lang="ts">
import { Check, Copy } from '@lucide/vue'
import { Button, Card } from '@repo/ui'
import { useClipboard } from '@vueuse/core'
import { MOCK_RECEIVERS, mockReceiverUrl } from '~/api/mock'

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
    <Card class="gap-0 py-0">
      <ul class="divide-y">
        <li
          v-for="receiver in MOCK_RECEIVERS"
          :key="receiver.path"
          class="flex items-start gap-2 px-3 py-2"
        >
          <div class="min-w-0 flex-1">
            <p class="truncate font-mono text-xs">/mock/{{ receiver.path }}</p>
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
    </Card>
  </section>
</template>
