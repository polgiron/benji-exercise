<script setup lang="ts">
import { Clock, FilePen, Lock, Mail, Server, VenetianMask } from '@lucide/vue'
import { BrandMark, cn } from '@repo/ui'
import {
  DEMO_SECRET,
  EFlowNode,
  EFlowScenario,
  EPacketState,
  type IFlowStep,
} from '~/utils/signature-flow'

interface Props {
  scenario: EFlowScenario
  step: IFlowStep
}

const props = defineProps<Props>()

const PACKETS = {
  [EPacketState.UNSIGNED]: { label: 'Unsigned', icon: Mail, tone: 'text-muted-foreground' },
  [EPacketState.SIGNED]: { label: 'Signed', icon: Lock, tone: 'border-primary/40 text-primary' },
  [EPacketState.TAMPERED]: {
    label: 'Edited',
    icon: FilePen,
    tone: 'border-destructive/40 text-destructive-foreground',
  },
  [EPacketState.STALE]: {
    label: '2 h old',
    icon: Clock,
    tone: 'border-warning/50 text-warning-foreground',
  },
}

const withAttacker = computed(() => props.scenario !== EFlowScenario.VALID)
const packet = computed(() => PACKETS[props.step.packet])
const compromised = computed(
  () => props.step.packet === EPacketState.TAMPERED || props.step.packet === EPacketState.STALE,
)

// The track spans the wire, ends on the node edges; the attacker hangs below its middle.
const packetPosition = computed(() => {
  const at = props.step.at
  if (at === EFlowNode.BENJI) return { left: '0%', top: '6rem' }
  if (at === EFlowNode.RECEIVER) return { left: '100%', top: '6rem' }
  return { left: '50%', top: withAttacker.value ? '13.5rem' : '6rem' }
})
</script>

<template>
  <div class="overflow-x-auto">
    <div
      class="relative mx-auto grid min-w-2xl grid-cols-[11rem_1fr_11rem] grid-rows-[10rem_auto] px-4 pt-4"
      role="img"
      :aria-label="`${step.title}. ${step.text}`"
    >
      <FlowNode
        class="self-center"
        title="Benji Webhooks"
        subtitle="Signs every attempt"
        :secret="DEMO_SECRET"
        :active="step.at === EFlowNode.BENJI"
      >
        <template #icon><BrandMark class="size-11" /></template>
      </FlowNode>

      <!-- The wire: traffic flows on it all the time, it turns red past a compromised hop. -->
      <div class="relative flex items-center" aria-hidden="true">
        <div class="h-0.5 flex-1 bg-wire text-primary/40 motion-safe:animate-wire" />
        <div
          :class="
            cn('h-0.5 flex-1 bg-wire transition-colors duration-500 motion-safe:animate-wire', {
              'text-primary/40': !compromised,
              'text-destructive/50': compromised,
            })
          "
        />
        <span
          class="absolute top-1/2 left-1/2 inline-flex -translate-x-1/2 -translate-y-[calc(100%+0.75rem)] items-center gap-1 rounded-badge bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground"
        >
          <Lock class="size-3" /> HTTPS
        </span>
      </div>

      <FlowNode
        class="self-center"
        title="Your endpoint"
        subtitle="acme.example/webhooks"
        :secret="DEMO_SECRET"
        :active="step.at === EFlowNode.RECEIVER"
        :verdict="step.verdict"
      >
        <template #icon><Server /></template>
      </FlowNode>

      <div class="col-start-2 flex flex-col items-center">
        <template v-if="withAttacker">
          <span class="h-10 border-l-2 border-dashed border-destructive/40" aria-hidden="true" />
          <FlowNode
            class="w-44"
            title="Someone on the path"
            subtitle="A proxy, an attacker"
            hostile
            :active="step.at === EFlowNode.ATTACKER"
          >
            <template #icon><VenetianMask /></template>
          </FlowNode>
        </template>
        <p v-else class="max-w-xs pt-2 pb-4 text-center text-xs text-muted-foreground">
          Both ends hold the same secret. It is shared once, when the endpoint is created, and never
          sent again.
        </p>
      </div>

      <!-- The request itself, gliding between the nodes. -->
      <div class="pointer-events-none absolute inset-y-0 right-62 left-62" aria-hidden="true">
        <div
          class="absolute z-10 -translate-x-1/2 -translate-y-1/2 transition-[left,top] duration-1000 ease-in-out-quart motion-reduce:transition-none"
          :style="packetPosition"
        >
          <div
            :key="step.packet"
            :class="
              cn(
                'flex items-center gap-1.5 rounded-full border bg-card px-3 py-1.5 text-xs font-medium whitespace-nowrap shadow-popover motion-safe:animate-rise',
                packet.tone,
              )
            "
          >
            <component :is="packet.icon" class="size-3.5" />
            <span class="font-mono text-foreground">POST</span>
            {{ packet.label }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
