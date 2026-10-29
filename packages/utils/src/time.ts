const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['day', 86_400],
  ['hour', 3_600],
  ['minute', 60],
  ['second', 1],
]

/** "3 minutes ago" / "in 12 seconds", relative to `now`. */
export function formatRelative(date: Date | string, now: Date = new Date()): string {
  const seconds = Math.round((new Date(date).getTime() - now.getTime()) / 1000)
  for (const [unit, size] of UNITS) {
    if (Math.abs(seconds) >= size || unit === 'second') {
      return rtf.format(Math.round(seconds / size), unit)
    }
  }
  return rtf.format(0, 'second')
}

/**
 * "3 minutes ago" for something that already happened. A clock that ticks once a second can
 * lag a fresh timestamp, which would read "in 1 second": clamp to "now" instead.
 */
export function formatAgo(date: Date | string, now: Date = new Date()): string {
  return formatRelative(new Date(Math.min(new Date(date).getTime(), now.getTime())), now)
}

/** 840 → "840 ms", 2300 → "2.3 s". */
export function formatDuration(ms: number): string {
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`
}
