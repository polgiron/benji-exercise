import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, nextTick } from 'vue'
import { publishEvent } from '~/api/events'
import { useFireEvent } from './use-fire-event'

vi.mock('~/api/events', () => ({
  publishEvent: vi.fn(async () => ({ deduplicated: false, event: {}, delivery_count: 1 })),
}))

function setup() {
  let form!: ReturnType<typeof useFireEvent>
  mount(
    defineComponent({
      setup() {
        form = useFireEvent()
        return () => null
      },
    }),
    { global: { plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]] } },
  )
  return form
}

async function fill(form: ReturnType<typeof useFireEvent>, payload: string) {
  form.eventType.value = 'campaign_updated'
  form.payloadText.value = payload
  await nextTick() // let the watcher hand out the key for this payload
}

describe('useFireEvent', () => {
  beforeEach(() => vi.mocked(publishEvent).mockClear())

  it('regenerates the key when the payload changes', async () => {
    const form = setup()
    await fill(form, '{"a": 1}')
    const key = form.idempotencyKey.value
    form.payloadText.value = '{"a": 2}'
    await nextTick()
    expect(form.idempotencyKey.value).not.toBe(key)
  })

  it('keeps the key on re-submit and moves on after a send', async () => {
    const form = setup()
    await fill(form, '{"a": 1}')
    const key = form.idempotencyKey.value

    form.send()
    await flushPromises()
    expect(form.idempotencyKey.value).not.toBe(key)

    form.resubmit()
    await flushPromises()
    const calls = vi.mocked(publishEvent).mock.calls
    expect(calls).toHaveLength(2)
    expect(calls[1]).toEqual(calls[0])
    expect(calls[1]![1]).toBe(key)
  })

  it('keeps the key when the send fails, so trying again is a retry', async () => {
    vi.mocked(publishEvent).mockRejectedValueOnce(new Error('network'))
    const form = setup()
    await fill(form, '{"a": 1}')
    const key = form.idempotencyKey.value
    form.send()
    await flushPromises()
    expect(form.idempotencyKey.value).toBe(key)
  })

  it('stops a payload that is not a JSON object before sending', async () => {
    const form = setup()
    await fill(form, '[1, 2]')
    form.send()
    expect(form.parseError.value).toMatch(/JSON object/)
    expect(publishEvent).not.toHaveBeenCalled()
  })
})
