<script setup lang="ts">
import { Check, KeyRound, X } from '@lucide/vue'
import { cn } from '@repo/ui'
import { EFlowVerdict } from '~/utils/signature-flow'

interface Props {
  title: string
  subtitle: string
  active?: boolean
  /** Shows the secret chip: only Benji and the receiver hold it. */
  secret?: string
  hostile?: boolean
  verdict?: EFlowVerdict
}

defineProps<Props>()
</script>

<template>
  <div class="relative">
    <!-- The spotlight: a ring that keeps swelling out while this node has the request. -->
    <span
      v-if="active"
      :class="
        cn('absolute inset-0 rounded-card border-2 motion-safe:animate-beacon', {
          'border-primary/50': !hostile,
          'border-destructive/50': hostile,
        })
      "
      aria-hidden="true"
    />
    <div
      :class="
        cn(
          'relative flex flex-col items-center gap-2 rounded-card border bg-card px-4 py-4 text-center shadow-card transition-[border-color,box-shadow,opacity] duration-500',
          {
            'border-primary/40 shadow-popover': active && !hostile,
            'border-destructive/40 shadow-popover': active && hostile,
            'border-success/60': verdict === EFlowVerdict.ACCEPTED,
            'border-destructive/60': verdict === EFlowVerdict.REJECTED,
          },
        )
      "
    >
      <span
        :class="
          cn(
            'grid size-11 place-items-center rounded-full transition-colors duration-500 [&_svg]:size-5',
            {
              'bg-accent text-accent-foreground': !hostile,
              'bg-destructive/10 text-destructive-foreground': hostile,
            },
          )
        "
      >
        <slot name="icon" />
      </span>
      <div class="min-w-0">
        <p class="text-sm font-semibold">{{ title }}</p>
        <p class="truncate text-xs text-muted-foreground">{{ subtitle }}</p>
      </div>
      <span
        v-if="secret"
        class="inline-flex max-w-full items-center gap-1 rounded-badge bg-secondary px-2 py-0.5 font-mono text-xs text-secondary-foreground"
        :title="`Signing secret: ${secret}`"
      >
        <KeyRound class="size-3 shrink-0 text-primary" />
        <span class="truncate">{{ secret.slice(0, 10) }}…</span>
      </span>
      <span
        v-else-if="hostile"
        class="inline-flex items-center gap-1 rounded-badge bg-destructive/10 px-2 py-0.5 text-xs font-medium text-destructive-foreground"
      >
        <KeyRound class="size-3" /> No secret
      </span>

      <Transition
        enter-from-class="scale-50 opacity-0"
        enter-active-class="transition duration-500 ease-out-quart motion-reduce:transition-none"
        leave-to-class="opacity-0"
        leave-active-class="transition duration-200"
      >
        <span
          v-if="verdict"
          :class="
            cn(
              'absolute -top-3 -right-3 grid size-7 place-items-center rounded-full text-primary-foreground shadow-popover',
              {
                'bg-success': verdict === EFlowVerdict.ACCEPTED,
                'bg-destructive': verdict === EFlowVerdict.REJECTED,
              },
            )
          "
          :aria-label="verdict === EFlowVerdict.ACCEPTED ? 'Accepted' : 'Rejected'"
        >
          <Check v-if="verdict === EFlowVerdict.ACCEPTED" class="size-4" />
          <X v-else class="size-4" />
        </span>
      </Transition>
    </div>
  </div>
</template>
