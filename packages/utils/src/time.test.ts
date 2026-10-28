import { describe, expect, it } from 'vitest'
import { formatDuration, formatRelative } from './time'

describe('formatRelative', () => {
  const now = new Date('2026-01-01T12:00:00Z')

  it('formats past and future times', () => {
    expect(formatRelative('2026-01-01T11:57:00Z', now)).toBe('3 minutes ago')
    expect(formatRelative('2026-01-01T12:00:12Z', now)).toBe('in 12 seconds')
  })
})

describe('formatDuration', () => {
  it('switches to seconds above 1000 ms', () => {
    expect(formatDuration(840)).toBe('840 ms')
    expect(formatDuration(2300)).toBe('2.3 s')
  })
})
