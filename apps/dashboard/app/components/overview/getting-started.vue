<script setup lang="ts">
import { ArrowRight, Check } from '@lucide/vue'
import { BrandMark, Button, Card, cn } from '@repo/ui'

const endpoints = useEndpoints()
const stats = useDeliveryStats()

const steps = computed(() => {
  const counts = stats.data.value
  if (!endpoints.data.value || !counts) return undefined
  return [
    {
      title: 'Add an endpoint',
      text: 'The URL that receives Benji events, signed with its own secret.',
      done: endpoints.data.value.length > 0,
      action: { to: '/endpoints?create', label: 'New endpoint' },
    },
    {
      title: 'Fire a test event',
      text: 'Pick an event type in the test panel on the right and send it.',
      done: counts.total > 0,
    },
    {
      title: 'Watch it land',
      text: 'Deliveries update live as they succeed, retry or fail.',
      done: counts.succeeded > 0,
      action: { to: '/deliveries', label: 'Open deliveries' },
    },
  ]
})

const doneCount = computed(() => steps.value?.filter((step) => step.done).length ?? 0)
// The step to do now: only it shows its button.
const current = computed(() => steps.value?.findIndex((step) => !step.done) ?? -1)
</script>

<template>
  <Card
    v-if="steps && current !== -1"
    class="relative gap-5 overflow-hidden border-primary/15 bg-linear-to-br from-accent/80 via-card to-card px-6"
  >
    <BrandMark
      class="pointer-events-none absolute -right-10 -bottom-14 size-48 rotate-12 opacity-10"
    />
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 class="text-lg font-semibold">Get your first webhook flowing</h2>
        <p class="text-sm text-muted-foreground">Three steps, about a minute.</p>
      </div>
      <div class="flex items-center gap-3 text-xs font-medium text-muted-foreground">
        {{ doneCount }} of {{ steps.length }} done
        <div class="h-1.5 w-24 overflow-hidden rounded-full bg-primary/15">
          <div
            class="h-full rounded-full bg-primary transition-[width] duration-700 ease-out-quart"
            :style="{ width: `${(doneCount / steps.length) * 100}%` }"
          />
        </div>
      </div>
    </div>
    <ol class="relative grid gap-3 md:grid-cols-3">
      <li
        v-for="(step, index) in steps"
        :key="step.title"
        :class="
          cn('flex gap-3 rounded-xl border bg-card/70 p-4 backdrop-blur-sm', {
            'border-primary/30 shadow-card': index === current,
          })
        "
      >
        <span
          :class="
            cn(
              'grid size-7 shrink-0 place-items-center rounded-full border text-xs font-semibold',
              {
                'border-primary bg-primary text-primary-foreground': step.done,
                'border-primary text-primary': index === current,
              },
            )
          "
        >
          <Check v-if="step.done" class="size-4" />
          <template v-else>{{ index + 1 }}</template>
        </span>
        <div class="min-w-0 space-y-1">
          <p :class="cn('text-sm font-medium', { 'text-muted-foreground': step.done })">
            {{ step.title }}
          </p>
          <p class="text-xs text-muted-foreground">{{ step.text }}</p>
          <Button v-if="step.action && index === current" size="sm" class="mt-2" as-child>
            <NuxtLink :to="step.action.to">{{ step.action.label }} <ArrowRight /></NuxtLink>
          </Button>
        </div>
      </li>
    </ol>
  </Card>
</template>
