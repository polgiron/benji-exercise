export interface IPoint {
  x: number
  y: number
}

/**
 * A y axis for counts: `intervals` equal steps of 1, 2 or 5 × 10ⁿ (never below 1, counts are
 * whole) whose top clears `max`. An all-zero series still gets a 0–4 axis.
 */
export function countScale(max: number, intervals = 4) {
  const rough = Math.max(max, 1) / intervals
  const magnitude = 10 ** Math.floor(Math.log10(rough))
  const step = Math.max(1, ([1, 2, 5, 10].find((m) => m * magnitude >= rough) ?? 10) * magnitude)
  return {
    top: step * intervals,
    ticks: Array.from({ length: intervals + 1 }, (_, i) => i * step),
  }
}

const sign = (value: number) => (value < 0 ? -1 : value > 0 ? 1 : 0)

/**
 * An SVG path through `points` as a monotone cubic curve (Steffen's method, like d3's
 * curveMonotoneX): smooth, yet never overshoots a point, so a count never dips below zero
 * or bulges past its peak between two buckets.
 */
export function smoothLine(points: IPoint[]): string {
  const [first] = points
  if (!first) return ''
  if (points.length === 1) return `M${first.x},${first.y}`

  const widths = points.slice(1).map((point, i) => point.x - points[i]!.x)
  const slopes = points.slice(1).map((point, i) => (point.y - points[i]!.y) / widths[i]!)
  const tangents = points.map((_, i) => {
    if (i === 0) return slopes[0]!
    if (i === points.length - 1) return slopes[i - 1]!
    const [before, after] = [slopes[i - 1]!, slopes[i]!]
    const [h0, h1] = [widths[i - 1]!, widths[i]!]
    const blended = (before * h1 + after * h0) / (h0 + h1)
    return (
      (sign(before) + sign(after)) *
      Math.min(Math.abs(before), Math.abs(after), 0.5 * Math.abs(blended))
    )
  })

  let path = `M${first.x},${first.y}`
  for (let i = 0; i < points.length - 1; i++) {
    const [from, to, third] = [points[i]!, points[i + 1]!, widths[i]! / 3]
    path +=
      `C${from.x + third},${from.y + tangents[i]! * third}` +
      ` ${to.x - third},${to.y - tangents[i + 1]! * third} ${to.x},${to.y}`
  }
  return path
}

/** The same curve, closed down to `baseline` to fill the area under it. */
export function smoothArea(points: IPoint[], baseline: number): string {
  const first = points[0]
  const last = points.at(-1)
  if (!first || !last) return ''
  return `${smoothLine(points)}L${last.x},${baseline}L${first.x},${baseline}Z`
}
