import { EDeliveryStatus, type IDeliveryStats } from '~/api/types'

export const DELIVERY_STATUS_LABELS: Record<EDeliveryStatus, string> = {
  [EDeliveryStatus.PENDING]: 'Pending',
  [EDeliveryStatus.IN_PROGRESS]: 'In progress',
  [EDeliveryStatus.SUCCEEDED]: 'Succeeded',
  [EDeliveryStatus.FAILED]: 'Failed',
}

const STATUSES = new Set<string>(Object.values(EDeliveryStatus))

export function isDeliveryStatus(value: unknown): value is EDeliveryStatus {
  return typeof value === 'string' && STATUSES.has(value)
}

/** `last_error` as a reader would say it; the worker's codes are terse. */
export function describeLastError(lastError: string | null): string | null {
  if (lastError === 'endpoint_disabled') return 'endpoint was disabled'
  return lastError
}

/** Settled deliveries (succeeded or failed) that succeeded, in %; undefined before any settle. */
export function successRate(stats: IDeliveryStats): number | undefined {
  const settled = stats.succeeded + stats.failed
  return settled > 0 ? (stats.succeeded / settled) * 100 : undefined
}
