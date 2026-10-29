import { describe, expect, it } from 'vitest'
import { EDeliveryStatus, type IDeliveryDetail, type IDeliverySummary } from '~/api/types'
import {
  EListMerge,
  attemptsGrew,
  mergeIntoDetail,
  mergeIntoList,
  statusChanged,
} from './deliveryCache'

function delivery(overrides: Partial<IDeliverySummary> = {}): IDeliverySummary {
  return {
    id: 'dlv_1',
    event_id: 'evt_1',
    event_type: 'campaign_updated',
    endpoint_id: 'ep_1',
    endpoint_url: 'http://localhost:8000/mock/ok',
    status: EDeliveryStatus.PENDING,
    attempt_count: 0,
    series_attempts: 0,
    max_attempts: 5,
    replay_count: 0,
    next_attempt_at: null,
    last_error: null,
    version: 1,
    created_at: '2026-10-29T09:00:00Z',
    updated_at: '2026-10-29T09:00:00Z',
    ...overrides,
  }
}

describe('mergeIntoList', () => {
  const other = delivery({ id: 'dlv_2' })

  it('applies a newer version in place', () => {
    const update = delivery({ version: 2, status: EDeliveryStatus.SUCCEEDED })
    const result = mergeIntoList([other, delivery()], {}, update)
    expect(result).toEqual({ action: EListMerge.PATCHED, list: [other, update] })
  })

  it('drops an older or equal version', () => {
    const cached = delivery({ version: 3 })
    for (const version of [2, 3]) {
      expect(mergeIntoList([cached], {}, delivery({ version })).action).toBe(EListMerge.UNCHANGED)
    }
  })

  it('patches the same row in two filtered lists', () => {
    const update = delivery({ version: 2, status: EDeliveryStatus.IN_PROGRESS })
    const byEndpoint = mergeIntoList([delivery()], { endpointId: 'ep_1' }, update)
    const unfiltered = mergeIntoList([other, delivery()], {}, update)
    expect(byEndpoint).toEqual({ action: EListMerge.PATCHED, list: [update] })
    expect(unfiltered).toEqual({ action: EListMerge.PATCHED, list: [other, update] })
  })

  it('removes a row that no longer matches the status filter', () => {
    const failed = delivery({ status: EDeliveryStatus.FAILED })
    const replayed = delivery({ version: 2, status: EDeliveryStatus.PENDING })
    const result = mergeIntoList([failed, other], { status: EDeliveryStatus.FAILED }, replayed)
    expect(result).toEqual({ action: EListMerge.PATCHED, list: [other] })
  })

  it('asks for a refetch for an unknown id that belongs in the list', () => {
    expect(mergeIntoList([other], {}, delivery()).action).toBe(EListMerge.REFETCH)
  })

  it('ignores an unknown id the filters exclude', () => {
    const result = mergeIntoList([other], { endpointId: 'ep_other' }, delivery())
    expect(result.action).toBe(EListMerge.UNCHANGED)
  })
})

describe('mergeIntoDetail', () => {
  const detail: IDeliveryDetail = { ...delivery(), payload: { a: 1 }, attempts: [] }

  it('updates the summary fields and keeps payload and attempts', () => {
    const update = delivery({ version: 2, status: EDeliveryStatus.FAILED })
    expect(mergeIntoDetail(detail, update)).toEqual({ ...update, payload: { a: 1 }, attempts: [] })
  })

  it('drops an update no newer than the detail', () => {
    expect(mergeIntoDetail(detail, delivery({ version: 1 }))).toBeUndefined()
  })
})

describe('statusChanged / attemptsGrew', () => {
  it('counts a delivery we never saw as a change', () => {
    expect(statusChanged(undefined, delivery())).toBe(true)
  })

  it('compares status only for a newer version', () => {
    const cached = delivery({ version: 2 })
    expect(statusChanged(cached, delivery({ version: 3, status: EDeliveryStatus.FAILED }))).toBe(
      true,
    )
    expect(statusChanged(cached, delivery({ version: 3 }))).toBe(false)
    expect(statusChanged(cached, delivery({ version: 1, status: EDeliveryStatus.FAILED }))).toBe(
      false,
    )
  })

  it('spots a new attempt', () => {
    expect(attemptsGrew(delivery(), delivery({ attempt_count: 1 }))).toBe(true)
    expect(attemptsGrew(delivery({ attempt_count: 1 }), delivery({ attempt_count: 1 }))).toBe(false)
  })
})
