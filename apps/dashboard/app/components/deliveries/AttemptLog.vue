<script setup lang="ts">
import { Badge, cn } from '@repo/ui'
import { formatDuration } from '@repo/utils'
import { EAttemptTrigger, type IAttempt } from '~/api/types'

interface Props {
  attempts: IAttempt[]
}

defineProps<Props>()

const isSuccess = (status: number | null) => !!status && status >= 200 && status < 300
</script>

<template>
  <p v-if="attempts.length === 0" class="text-xs text-muted-foreground">
    No attempt yet: the worker picks it up within a second.
  </p>
  <ol v-else class="divide-y rounded-md border bg-card">
    <li v-for="attempt in attempts" :key="attempt.id" class="space-y-1 px-3 py-2 text-xs">
      <div class="flex flex-wrap items-center gap-2">
        <span class="font-medium">#{{ attempt.number }}</span>
        <Badge v-if="attempt.trigger === EAttemptTrigger.REPLAY" variant="secondary">replay</Badge>
        <span
          :class="
            cn('font-mono', {
              'text-success-foreground': isSuccess(attempt.response_status),
              'text-destructive-foreground': !isSuccess(attempt.response_status),
            })
          "
        >
          {{ attempt.response_status ?? attempt.error ?? '—' }}
        </span>
        <span class="text-muted-foreground">{{ formatDuration(attempt.duration_ms) }}</span>
        <span class="ml-auto text-muted-foreground" :title="attempt.started_at">
          {{ new Date(attempt.started_at).toLocaleTimeString() }}
        </span>
      </div>
      <p
        v-if="attempt.response_body"
        class="truncate font-mono text-2xs text-muted-foreground"
        :title="attempt.response_body"
      >
        {{ attempt.response_body }}
      </p>
    </li>
  </ol>
</template>
