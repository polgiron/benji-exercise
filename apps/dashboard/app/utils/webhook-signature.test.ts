import { describe, expect, it } from 'vitest'
import { signWebhook } from './webhook-signature'

const SECRET = 'whsec_MfKQ9r8GKYqrTwjUPD8ILPZIo2LaLaSw'
const TIMESTAMP = 1793264400

// Expected values come from the API's own `app.signing.sign()`, so the two can't drift apart.
describe('signWebhook', () => {
  it('matches the API signature for the same id, timestamp and body', async () => {
    const body = '{"type":"reward_transaction_created","points":50}'
    expect(await signWebhook(SECRET, 'dlv_demo', TIMESTAMP, body)).toBe(
      'v1,KVv46M5nPz1ZlplLz+7VA4w7IdUP9q7xkHdkPNd9MmY=',
    )
  })

  it('signs the UTF-8 bytes of the body', async () => {
    expect(await signWebhook(SECRET, 'dlv_demo', TIMESTAMP, '{"points":50,"note":"café"}')).toBe(
      'v1,VCsWV0HwyKvSf9DlkMolLbBqYn//s29pjiwg77qIO5E=',
    )
  })

  it('changes when a single byte of the body changes', async () => {
    const signed = await signWebhook(SECRET, 'dlv_demo', TIMESTAMP, '{"points":50}')
    expect(await signWebhook(SECRET, 'dlv_demo', TIMESTAMP, '{"points":5000}')).not.toBe(signed)
  })
})
