<script setup lang="ts">
import { Check, Pause, Play, RotateCcw } from '@lucide/vue'
import {
  Button,
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  cn,
  Tabs,
  TabsList,
  TabsTrigger,
} from '@repo/ui'
import { computedAsync, usePreferredReducedMotion, useTimeoutFn } from '@vueuse/core'
import {
  DEMO_BODY,
  DEMO_DELIVERY_ID,
  DEMO_SECRET,
  DEMO_TIMESTAMP,
  EFlowScenario,
  EPacketState,
  FLOW_SCENARIO_LABELS,
  FLOW_SCENARIOS,
  isFlowScenario,
  TAMPERED_BODY,
} from '~/utils/signature-flow'
import { signWebhook } from '~/utils/webhook-signature'

const STEP_MS = 4200

const scenario = ref(EFlowScenario.VALID)
const index = ref(0)
const steps = computed(() => FLOW_SCENARIOS[scenario.value])
const step = computed(() => steps.value[index.value] ?? steps.value[0]!)
const last = computed(() => index.value === steps.value.length - 1)

// Plays by itself, unless the OS asks for less motion: then it waits for a click.
const reducedMotion = usePreferredReducedMotion()
const playing = ref(reducedMotion.value !== 'reduce')

const timer = useTimeoutFn(() => index.value++, STEP_MS, { immediate: false })
// Restarted on every change, so a clicked step or a new tab gets its full time on screen.
watch(
  [scenario, index, playing],
  () => {
    if (playing.value && last.value) playing.value = false
    if (playing.value) timer.start()
    else timer.stop()
  },
  { immediate: true },
)

function selectScenario(value: EFlowScenario) {
  scenario.value = value
  index.value = 0
  playing.value = reducedMotion.value !== 'reduce'
}

function goTo(target: number) {
  index.value = target
  playing.value = false
}

function togglePlay() {
  if (!playing.value && last.value) index.value = 0
  playing.value = !playing.value
}

// Signed for real with Web Crypto: the same HMAC the API and a receiver compute.
const signature = computedAsync(() =>
  signWebhook(DEMO_SECRET, DEMO_DELIVERY_ID, DEMO_TIMESTAMP, DEMO_BODY),
)
const expected = computedAsync(() =>
  signWebhook(
    DEMO_SECRET,
    DEMO_DELIVERY_ID,
    DEMO_TIMESTAMP,
    step.value.packet === EPacketState.TAMPERED ? TAMPERED_BODY : DEMO_BODY,
  ),
)
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Follow one delivery</CardTitle>
      <CardDescription
        >What Benji sends, and what your endpoint checks before trusting it.</CardDescription
      >
      <CardAction>
        <Tabs
          :model-value="scenario"
          @update:model-value="(value) => isFlowScenario(value) && selectScenario(value)"
        >
          <TabsList>
            <TabsTrigger
              v-for="option in Object.values(EFlowScenario)"
              :key="option"
              :value="option"
              class="px-3"
            >
              {{ FLOW_SCENARIO_LABELS[option] }}
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </CardAction>
    </CardHeader>
    <CardContent class="space-y-6">
      <FlowDiagram :scenario="scenario" :step="step" class="rounded-card bg-dots" />

      <div class="grid gap-6 lg:grid-cols-5">
        <div class="space-y-4 lg:col-span-2">
          <ol class="space-y-1">
            <li v-for="(item, itemIndex) in steps" :key="`${scenario}-${item.title}`">
              <button
                type="button"
                :aria-current="itemIndex === index ? 'step' : undefined"
                :class="
                  cn(
                    'relative flex w-full gap-3 overflow-hidden rounded-lg px-3 py-2 text-left transition-colors hover:bg-muted',
                    { 'bg-accent/60 hover:bg-accent/60': itemIndex === index },
                  )
                "
                @click="goTo(itemIndex)"
              >
                <span
                  :class="
                    cn(
                      'mt-0.5 grid size-5 shrink-0 place-items-center rounded-full border text-xs font-semibold transition-colors',
                      {
                        'border-primary bg-primary text-primary-foreground': itemIndex < index,
                        'border-primary text-primary': itemIndex === index,
                        'text-muted-foreground': itemIndex > index,
                      },
                    )
                  "
                >
                  <Check v-if="itemIndex < index" class="size-3" />
                  <template v-else>{{ itemIndex + 1 }}</template>
                </span>
                <span class="min-w-0 space-y-1">
                  <span
                    :class="
                      cn('block text-sm font-medium', {
                        'text-muted-foreground': itemIndex !== index,
                      })
                    "
                  >
                    {{ item.title }}
                  </span>
                  <span v-if="itemIndex === index" class="block text-xs text-muted-foreground">
                    {{ item.text }}
                  </span>
                </span>
                <!-- How long until the next step, while playing. -->
                <span
                  v-if="itemIndex === index && playing"
                  :key="`${scenario}-${index}`"
                  class="absolute inset-x-0 bottom-0 h-0.5 bg-primary/60 animate-reveal"
                  :style="{ animationDuration: `${STEP_MS}ms`, animationTimingFunction: 'linear' }"
                  aria-hidden="true"
                />
              </button>
            </li>
          </ol>
          <div class="flex items-center gap-2 px-3">
            <Button size="sm" @click="togglePlay">
              <Pause v-if="playing" />
              <RotateCcw v-else-if="last" />
              <Play v-else />
              {{ playing ? 'Pause' : last ? 'Replay' : 'Play' }}
            </Button>
            <span class="text-xs text-muted-foreground tabular-nums">
              Step {{ index + 1 }} of {{ steps.length }}
            </span>
          </div>
        </div>

        <SignedRequest
          class="lg:col-span-3"
          :step="step"
          :signature="signature"
          :expected="expected"
        />
      </div>
    </CardContent>
  </Card>
</template>
