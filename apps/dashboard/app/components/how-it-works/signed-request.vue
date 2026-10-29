<script setup lang="ts">
import { Check, Minus, X } from '@lucide/vue'
import { cn } from '@repo/ui'
import {
  DEMO_BODY,
  DEMO_DELIVERY_ID,
  DEMO_TIMESTAMP,
  EFlowNode,
  EFlowVerdict,
  EPacketState,
  ERequestPart,
  REPLAY_DELAY_SECONDS,
  TAMPERED_BODY,
  TOLERANCE_SECONDS,
  type IFlowStep,
} from '~/utils/signature-flow'

interface Props {
  step: IFlowStep
  /** What Benji put in `webhook-signature`; undefined until Web Crypto has computed it. */
  signature?: string
  /** What the receiver computes over the bytes it got. */
  expected?: string
}

const props = defineProps<Props>()

const TAMPERED_FIELD = '"points":5000'

const tampered = computed(() => props.step.packet === EPacketState.TAMPERED)
const signed = computed(() => props.step.packet !== EPacketState.UNSIGNED)
const lit = (part: ERequestPart) => props.step.focus.includes(part)

const headers = computed(() => [
  { part: undefined, name: 'content-type', value: 'application/json' },
  { part: ERequestPart.ID, name: 'webhook-id', value: DEMO_DELIVERY_ID },
  { part: ERequestPart.TIMESTAMP, name: 'webhook-timestamp', value: String(DEMO_TIMESTAMP) },
  {
    part: ERequestPart.SIGNATURE,
    name: 'webhook-signature',
    value: signed.value ? (props.signature ?? '…') : 'not signed yet',
  },
])
// Split around the edited field so it can be marked; the untouched body is one piece.
const bodyParts = computed(() =>
  tampered.value ? TAMPERED_BODY.split(TAMPERED_FIELD) : [DEMO_BODY],
)

// The receiver's side, as `verify()` in apps/api/app/signing.py runs it: freshness first.
const atReceiver = computed(() => props.step.at === EFlowNode.RECEIVER)
const age = computed(() => (props.step.packet === EPacketState.STALE ? REPLAY_DELAY_SECONDS : 2))
const fresh = computed(() => age.value <= TOLERANCE_SECONDS)
const signatureChecked = computed(() => !!props.step.verdict && fresh.value)
const signatureMatches = computed(() => !!props.signature && props.signature === props.expected)
</script>

<template>
  <div class="space-y-3">
    <div class="overflow-hidden rounded-input border bg-muted font-mono text-xs leading-relaxed">
      <div class="border-b px-3 py-2 text-foreground">
        <span class="font-semibold text-primary">POST</span> https://acme.example/webhooks
      </div>
      <div class="py-1">
        <div
          v-for="header in headers"
          :key="header.name"
          :class="
            cn('flex gap-2 px-3 transition-colors duration-500', {
              'bg-primary/10': header.part && lit(header.part),
            })
          "
        >
          <span class="shrink-0 text-muted-foreground">{{ header.name }}:</span>
          <span
            :class="
              cn('min-w-0 truncate text-foreground', {
                'text-muted-foreground italic': header.part === ERequestPart.SIGNATURE && !signed,
              })
            "
          >
            {{ header.value }}
          </span>
        </div>
      </div>
      <p
        :class="
          cn('border-t px-3 py-2 break-all text-foreground transition-colors duration-500', {
            'bg-primary/10': lit(ERequestPart.BODY) && !tampered,
            'bg-destructive/10': lit(ERequestPart.BODY) && tampered,
          })
        "
      >
        <template v-for="(part, index) in bodyParts" :key="index">
          <mark
            v-if="index > 0"
            class="rounded-xs bg-destructive/20 px-0.5 font-semibold text-destructive-foreground"
            >{{ TAMPERED_FIELD }}</mark
          >{{ part }}
        </template>
      </p>
    </div>

    <Transition
      enter-from-class="opacity-0 translate-y-2"
      enter-active-class="transition duration-500 ease-out-quart motion-reduce:transition-none"
    >
      <dl v-if="atReceiver" class="space-y-2 rounded-input border p-3 text-xs">
        <div class="flex items-start gap-2">
          <component
            :is="fresh ? Check : X"
            :class="
              cn('mt-0.5 size-3.5 shrink-0', { 'text-success': fresh, 'text-destructive': !fresh })
            "
          />
          <dt class="w-24 shrink-0 font-medium">Timestamp</dt>
          <dd class="text-muted-foreground">
            Sent {{ age < 60 ? `${age} s` : `${age / 3600} h` }} ago:
            {{ fresh ? 'within' : 'outside' }} the {{ TOLERANCE_SECONDS / 60 }} minute tolerance
          </dd>
        </div>
        <div v-if="step.verdict" class="flex items-start gap-2">
          <component
            :is="!signatureChecked ? Minus : signatureMatches ? Check : X"
            :class="
              cn('mt-0.5 size-3.5 shrink-0', {
                'text-muted-foreground': !signatureChecked,
                'text-success': signatureChecked && signatureMatches,
                'text-destructive': signatureChecked && !signatureMatches,
              })
            "
          />
          <dt class="w-24 shrink-0 font-medium">Signature</dt>
          <dd v-if="signatureChecked" class="min-w-0 space-y-0.5 text-muted-foreground">
            <p>Recomputed over the bytes received:</p>
            <p
              :class="
                cn('truncate font-mono', {
                  'text-success-foreground': signatureMatches,
                  'text-destructive-foreground': !signatureMatches,
                })
              "
            >
              {{ expected ?? '…' }}
            </p>
          </dd>
          <dd v-else class="text-muted-foreground">Not checked: the request was already refused</dd>
        </div>
        <div v-if="step.response" class="flex items-start gap-2 border-t pt-2">
          <span class="size-3.5 shrink-0" />
          <dt class="w-24 shrink-0 font-medium">Response</dt>
          <dd
            :class="
              cn('font-mono', {
                'text-success-foreground': step.verdict === EFlowVerdict.ACCEPTED,
                'text-destructive-foreground': step.verdict === EFlowVerdict.REJECTED,
              })
            "
          >
            {{ step.response }}
          </dd>
        </div>
      </dl>
    </Transition>
  </div>
</template>
