import { EActivityRange } from '~/api/types'

export const ACTIVITY_RANGE_LABELS: Record<EActivityRange, string> = {
  [EActivityRange.DAY]: 'Last 24 hours',
  [EActivityRange.WEEK]: 'Last 7 days',
  [EActivityRange.MONTH]: 'Last 30 days',
}

/** What one bucket of each range spans, for the chart's description. */
export const ACTIVITY_BUCKET_LABELS: Record<EActivityRange, string> = {
  [EActivityRange.DAY]: 'per hour',
  [EActivityRange.WEEK]: 'per 6 hours',
  [EActivityRange.MONTH]: 'per day',
}

const RANGES = new Set<string>(Object.values(EActivityRange))

export function isActivityRange(value: unknown): value is EActivityRange {
  return typeof value === 'string' && RANGES.has(value)
}

const TICK_FORMATS: Record<EActivityRange, Intl.DateTimeFormat> = {
  [EActivityRange.DAY]: new Intl.DateTimeFormat('en', { hour: 'numeric' }),
  [EActivityRange.WEEK]: new Intl.DateTimeFormat('en', { weekday: 'short', day: 'numeric' }),
  [EActivityRange.MONTH]: new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }),
}

const DAY_FORMAT = new Intl.DateTimeFormat('en', {
  weekday: 'short',
  month: 'short',
  day: 'numeric',
})
const TIME_FORMAT = new Intl.DateTimeFormat('en', { hour: '2-digit', minute: '2-digit' })

/** An x-axis label: "14:00", "Wed 29" or "Oct 29", in the viewer's time zone. */
export function formatActivityTick(start: string, range: EActivityRange): string {
  return TICK_FORMATS[range].format(new Date(start))
}

/** A bucket as the tooltip names it: "Wed, Oct 29, 14:00 – 15:00", or the day alone. */
export function formatActivityBucket(start: string, bucketSeconds: number): string {
  const from = new Date(start)
  if (bucketSeconds >= 86_400) return DAY_FORMAT.format(from)
  const to = new Date(from.getTime() + bucketSeconds * 1000)
  return `${DAY_FORMAT.format(from)}, ${TIME_FORMAT.format(from)} – ${TIME_FORMAT.format(to)}`
}
