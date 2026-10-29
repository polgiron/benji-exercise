<script setup lang="ts">
import { EActivityRange, type IDeliveryActivity } from '~/api/types'
import { formatActivityBucket, formatActivityTick, isActivityRange } from '~/utils/activity'
import { countScale, smoothArea, smoothLine } from '~/utils/chart'

interface Props {
  activity: IDeliveryActivity
}

const props = defineProps<Props>()

// The SVG draws in this box and is stretched to fit (`preserveAspectRatio="none"`); strokes keep
// their width through `vector-effect`, and the dot, tooltip and labels are HTML placed in %.
const W = 1000
const H = 300
const MAX_TICKS = 7

const gradientId = useId()
const plot = useTemplateRef<HTMLElement>('plot')
const hovered = ref<number>()

const buckets = computed(() => props.activity.buckets)
// The schema types it as a literal union; the formatters key on the enum.
const range = computed(() =>
  isActivityRange(props.activity.range) ? props.activity.range : EActivityRange.WEEK,
)
const total = computed(() => buckets.value.reduce((sum, b) => sum + b.total, 0))
const scale = computed(() => countScale(Math.max(0, ...buckets.value.map((b) => b.total))))

const x = (index: number) =>
  buckets.value.length > 1 ? (index / (buckets.value.length - 1)) * W : W / 2
const y = (count: number) => H - (count / scale.value.top) * H

const totalPoints = computed(() => buckets.value.map((b, i) => ({ x: x(i), y: y(b.total) })))
const line = computed(() => smoothLine(totalPoints.value))
const area = computed(() => smoothArea(totalPoints.value, H))
const failedLine = computed(() =>
  buckets.value.some((b) => b.failed > 0)
    ? smoothLine(buckets.value.map((b, i) => ({ x: x(i), y: y(b.failed) })))
    : '',
)

// At rest the dot sits on the busiest bucket, like the Pilot chart; hovering moves it.
const peak = computed(() => {
  let best: number | undefined
  buckets.value.forEach((bucket, index) => {
    if (bucket.total > 0 && (best === undefined || bucket.total >= buckets.value[best]!.total)) {
      best = index
    }
  })
  return best
})
const focusIndex = computed(() => hovered.value ?? peak.value)
const focus = computed(() => {
  const index = focusIndex.value
  const bucket = index === undefined ? undefined : buckets.value[index]
  if (index === undefined || !bucket) return undefined
  return { bucket, left: (x(index) / W) * 100, top: (y(bucket.total) / H) * 100 }
})

// Counted back from the newest bucket, so "now" always gets a label.
const ticks = computed(() => {
  const step = Math.ceil(buckets.value.length / MAX_TICKS)
  return buckets.value
    .map((bucket, index) => ({ bucket, index }))
    .filter(({ index }) => (buckets.value.length - 1 - index) % step === 0)
})

const compact = new Intl.NumberFormat('en', { notation: 'compact' })

function onPointerMove(event: PointerEvent) {
  const rect = plot.value?.getBoundingClientRect()
  if (!rect || buckets.value.length === 0) return
  const ratio = (event.clientX - rect.left) / rect.width
  hovered.value = Math.min(
    buckets.value.length - 1,
    Math.max(0, Math.round(ratio * (buckets.value.length - 1))),
  )
}
</script>

<template>
  <div class="flex h-64 gap-3 select-none">
    <div class="relative mb-6 w-10 shrink-0 text-xs text-muted-foreground tabular-nums">
      <span
        v-for="tick in scale.ticks"
        :key="tick"
        class="absolute right-0 -translate-y-1/2"
        :style="{ top: `${100 - (tick / scale.top) * 100}%` }"
      >
        {{ compact.format(tick) }}
      </span>
    </div>

    <div class="flex min-w-0 flex-1 flex-col">
      <div
        ref="plot"
        class="relative flex-1"
        role="img"
        :aria-label="`${total} deliveries in this window`"
        @pointermove="onPointerMove"
        @pointerleave="hovered = undefined"
      >
        <svg
          class="absolute inset-0 size-full overflow-visible"
          :viewBox="`0 0 ${W} ${H}`"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <line
            v-for="tick in scale.ticks"
            :key="tick"
            x1="0"
            :x2="W"
            :y1="y(tick)"
            :y2="y(tick)"
            class="stroke-border"
            stroke-dasharray="4 4"
            vector-effect="non-scaling-stroke"
          />
          <line
            v-if="hovered !== undefined"
            :x1="x(hovered)"
            :x2="x(hovered)"
            y1="0"
            :y2="H"
            class="stroke-primary/30"
            vector-effect="non-scaling-stroke"
          />
        </svg>

        <!-- Keyed by range: a new range draws in again from the left. -->
        <svg
          :key="range"
          class="absolute inset-0 size-full overflow-visible motion-safe:animate-reveal"
          :viewBox="`0 0 ${W} ${H}`"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <defs>
            <linearGradient :id="gradientId" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" class="[stop-color:var(--color-chart-1)]" stop-opacity="0.22" />
              <stop offset="100%" class="[stop-color:var(--color-chart-1)]" stop-opacity="0" />
            </linearGradient>
          </defs>
          <path :d="area" :fill="`url(#${gradientId})`" />
          <path
            v-if="failedLine"
            :d="failedLine"
            fill="none"
            class="stroke-chart-4"
            stroke-width="1.75"
            stroke-dasharray="6 5"
            stroke-linecap="round"
            vector-effect="non-scaling-stroke"
          />
          <path
            :d="line"
            fill="none"
            class="stroke-chart-1"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
            vector-effect="non-scaling-stroke"
          />
        </svg>

        <template v-if="focus">
          <span
            class="pointer-events-none absolute size-3.5 -translate-1/2 rounded-full border-[3px] border-chart-1 bg-card shadow-card transition-[left,top] duration-150 ease-out-quart motion-reduce:transition-none"
            :style="{ left: `${focus.left}%`, top: `${focus.top}%` }"
          />
          <div
            v-if="hovered !== undefined"
            class="pointer-events-none absolute z-10 w-max rounded-popover border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-popover"
            :style="{
              left: `${Math.min(85, Math.max(15, focus.left))}%`,
              top: `${focus.top}%`,
              transform:
                focus.top < 35 ? 'translate(-50%, 16px)' : 'translate(-50%, calc(-100% - 16px))',
            }"
          >
            <p class="font-medium">
              {{ formatActivityBucket(focus.bucket.start, activity.bucket_seconds) }}
            </p>
            <dl class="mt-1.5 grid grid-cols-[auto_auto] gap-x-6 gap-y-0.5 text-muted-foreground">
              <dt class="flex items-center gap-2">
                <span class="size-2 rounded-full bg-chart-1" /> Deliveries
              </dt>
              <dd class="text-right font-semibold text-foreground tabular-nums">
                {{ focus.bucket.total }}
              </dd>
              <dt class="flex items-center gap-2">
                <span class="size-2 rounded-full bg-success" /> Succeeded
              </dt>
              <dd class="text-right font-semibold text-foreground tabular-nums">
                {{ focus.bucket.succeeded }}
              </dd>
              <dt class="flex items-center gap-2">
                <span class="size-2 rounded-full bg-chart-4" /> Failed
              </dt>
              <dd class="text-right font-semibold text-foreground tabular-nums">
                {{ focus.bucket.failed }}
              </dd>
            </dl>
          </div>
        </template>
      </div>

      <div class="relative h-6 text-xs text-muted-foreground">
        <span
          v-for="tick in ticks"
          :key="tick.bucket.start"
          class="absolute top-2 -translate-x-1/2 whitespace-nowrap"
          :style="{ left: `${(x(tick.index) / W) * 100}%` }"
        >
          {{ formatActivityTick(tick.bucket.start, range) }}
        </span>
      </div>
    </div>
  </div>
</template>
