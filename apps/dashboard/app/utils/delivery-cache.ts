import type { IDeliveryDetail, IDeliveryFilters, IDeliverySummary } from '~/api/types'

// How a `delivery.updated` lands in the cache. Pure, no Vue: useDeliveryCache applies the
// result. Every rule hangs on `version`, which only grows: an update not newer than the
// copy we hold is dropped, so a late or replayed message can't regress a row.

export enum EListMerge {
  /** Nothing to do: the row isn't here and doesn't belong, or our copy is as new. */
  UNCHANGED = 'unchanged',
  PATCHED = 'patched',
  /** A row this list should show but doesn't hold: refetch rather than guess its place. */
  REFETCH = 'refetch',
}

export type IListMergeResult =
  | { action: EListMerge.UNCHANGED | EListMerge.REFETCH }
  | { action: EListMerge.PATCHED; list: IDeliverySummary[] }

export function matchesFilters(delivery: IDeliverySummary, filters: IDeliveryFilters): boolean {
  return (
    (!filters.status || delivery.status === filters.status) &&
    (!filters.endpointId || delivery.endpoint_id === filters.endpointId) &&
    (!filters.eventType || delivery.event_type === filters.eventType)
  )
}

export function mergeIntoList(
  list: IDeliverySummary[],
  filters: IDeliveryFilters,
  update: IDeliverySummary,
): IListMergeResult {
  const index = list.findIndex((row) => row.id === update.id)
  if (index === -1) {
    return { action: matchesFilters(update, filters) ? EListMerge.REFETCH : EListMerge.UNCHANGED }
  }
  if (list[index]!.version >= update.version) return { action: EListMerge.UNCHANGED }
  // A row filtered by status leaves the list when its status moves on (failed → pending on
  // replay); dropping it is exact, unlike inserting one.
  const next = matchesFilters(update, filters) ? list.with(index, update) : list.toSpliced(index, 1)
  return { action: EListMerge.PATCHED, list: next }
}

/** The summary fields of a cached detail, or undefined when ours is as new. */
export function mergeIntoDetail(
  detail: IDeliveryDetail,
  update: IDeliverySummary,
): IDeliveryDetail | undefined {
  if (detail.version >= update.version) return undefined
  return { ...detail, ...update }
}

/** The summary doesn't carry attempts: a new one recorded means the detail's log is behind. */
export function attemptsGrew(previous: IDeliverySummary, update: IDeliverySummary): boolean {
  return update.attempt_count > previous.attempt_count
}

/**
 * Whether the counts by status can have moved. Unknown to us (a new delivery) counts as a
 * change; an update no newer than what we hold does not.
 */
export function statusChanged(
  previous: IDeliverySummary | undefined,
  update: IDeliverySummary,
): boolean {
  if (!previous) return true
  return previous.version < update.version && previous.status !== update.status
}
