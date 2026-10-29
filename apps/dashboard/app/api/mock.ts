export interface IMockReceiver {
  path: string
  answer: string
  does: string
}

export const MOCK_RECEIVERS: IMockReceiver[] = [
  { path: 'ok', answer: '200', does: 'Accepts every delivery.' },
  { path: 'flaky?fail=2', answer: '503 ×2, then 200', does: 'Succeeds on the 3rd attempt.' },
  { path: 'fail', answer: '500', does: 'Retried until attempts run out, then failed.' },
  { path: 'reject', answer: '400', does: 'Terminal: failed at once, no retry.' },
  { path: 'slow?seconds=15', answer: 'after 15 s', does: 'Times out (10 s) and is retried.' },
]

// The worker POSTs to these, not the dashboard: it only needs their URLs to paste into an endpoint.
export const mockReceiverUrl = (pathAndQuery: string) =>
  `${useRuntimeConfig().public.apiBase}/mock/${pathAndQuery}`
