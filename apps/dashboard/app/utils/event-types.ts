import { EEventType } from '~/api/types'

const EVENT_TYPES = new Set<string>(Object.values(EEventType))

export function isEventType(value: unknown): value is EEventType {
  return typeof value === 'string' && EVENT_TYPES.has(value)
}
