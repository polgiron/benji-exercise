import { useQueryClient } from '@tanstack/vue-query'
import type { IDeliveryDetail, IDeliveryFilters, IDeliverySummary } from '~/api/types'
import {
  EListMerge,
  attemptsGrew,
  mergeIntoDetail,
  mergeIntoList,
  statusChanged,
} from '~/utils/delivery-cache'
import { deliveryKeys } from './query-keys'

// An event fanned out to 5 endpoints arrives as 5 updates in a burst: one refetch covers them.
const REFETCH_DEBOUNCE_MS = 250

/** Writes delivery summaries (from the stream, or a replay response) into every cached view. */
export function useDeliveryCache() {
  const queryClient = useQueryClient()
  const due = { lists: false, stats: false }
  let timer: ReturnType<typeof setTimeout> | undefined

  function scheduleRefetch(what: keyof typeof due) {
    due[what] = true
    clearTimeout(timer)
    timer = setTimeout(() => {
      if (due.lists) queryClient.invalidateQueries({ queryKey: deliveryKeys.lists() })
      if (due.stats) queryClient.invalidateQueries({ queryKey: deliveryKeys.stats() })
      due.lists = due.stats = false
    }, REFETCH_DEBOUNCE_MS)
  }

  function apply(update: IDeliverySummary) {
    const detailKey = deliveryKeys.detail(update.id)
    const detail = queryClient.getQueryData<IDeliveryDetail>(detailKey)
    let previous: IDeliverySummary | undefined = detail

    const lists = queryClient.getQueriesData<IDeliverySummary[]>({
      queryKey: deliveryKeys.lists(),
    })
    for (const [key, list] of lists) {
      if (!list) continue
      const row = list.find((d) => d.id === update.id)
      if (row && (!previous || row.version > previous.version)) previous = row
      // deliveryKeys.list puts the filters third.
      const result = mergeIntoList(list, key[2] as IDeliveryFilters, update)
      if (result.action === EListMerge.PATCHED) queryClient.setQueryData(key, result.list)
      if (result.action === EListMerge.REFETCH) scheduleRefetch('lists')
    }

    const merged = detail && mergeIntoDetail(detail, update)
    if (merged) {
      queryClient.setQueryData(detailKey, merged)
      if (attemptsGrew(detail, update)) queryClient.invalidateQueries({ queryKey: detailKey })
    }

    if (statusChanged(previous, update)) scheduleRefetch('stats')
  }

  return { apply }
}
