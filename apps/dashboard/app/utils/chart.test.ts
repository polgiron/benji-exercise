import { describe, expect, it } from 'vitest'
import { countScale, smoothArea, smoothLine } from './chart'

describe('countScale', () => {
  it('gives an empty series a 0–4 axis of whole steps', () => {
    expect(countScale(0)).toEqual({ top: 4, ticks: [0, 1, 2, 3, 4] })
  })

  it('rounds the top up to a nice step that clears the max', () => {
    expect(countScale(7).ticks).toEqual([0, 2, 4, 6, 8])
    expect(countScale(30).top).toBe(40)
    expect(countScale(31_000).ticks).toEqual([0, 10_000, 20_000, 30_000, 40_000])
  })

  it('never steps by a fraction of a delivery', () => {
    expect(countScale(2).ticks).toEqual([0, 1, 2, 3, 4])
  })
})

describe('smoothLine', () => {
  it('starts at the first point and ends at the last', () => {
    const path = smoothLine([
      { x: 0, y: 10 },
      { x: 10, y: 0 },
      { x: 20, y: 5 },
    ])
    expect(path.startsWith('M0,10')).toBe(true)
    expect(path.endsWith(' 20,5')).toBe(true)
  })

  it('keeps a flat run flat: no control point leaves the line', () => {
    const path = smoothLine([
      { x: 0, y: 50 },
      { x: 10, y: 50 },
      { x: 20, y: 50 },
    ])
    const ys = [...path.matchAll(/,(-?[\d.]+)/g)].map((m) => Number(m[1]))
    expect(new Set(ys)).toEqual(new Set([50]))
  })

  it('does not overshoot a peak', () => {
    const path = smoothLine([
      { x: 0, y: 100 },
      { x: 10, y: 0 },
      { x: 20, y: 100 },
      { x: 30, y: 100 },
    ])
    const ys = [...path.matchAll(/,(-?[\d.]+)/g)].map((m) => Number(m[1]))
    expect(Math.min(...ys)).toBe(0)
    expect(Math.max(...ys)).toBe(100)
  })

  it('handles no point and one point', () => {
    expect(smoothLine([])).toBe('')
    expect(smoothLine([{ x: 3, y: 4 }])).toBe('M3,4')
  })
})

describe('smoothArea', () => {
  it('closes the curve down to the baseline', () => {
    const area = smoothArea(
      [
        { x: 0, y: 1 },
        { x: 10, y: 2 },
      ],
      100,
    )
    expect(area.endsWith('L10,100L0,100Z')).toBe(true)
  })
})
