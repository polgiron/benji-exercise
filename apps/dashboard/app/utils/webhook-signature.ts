const SECRET_PREFIX = 'whsec_'

const toBase64 = (bytes: Uint8Array) => btoa(String.fromCharCode(...bytes))
const fromBase64 = (text: string) => Uint8Array.from(atob(text), (char) => char.charCodeAt(0))

/**
 * The browser twin of `sign()` in `apps/api/app/signing.py` (Standard Webhooks): the "How it works"
 * page signs its demo request for real, so the signatures it shows are the ones a receiver checks.
 */
export async function signWebhook(
  secret: string,
  msgId: string,
  timestamp: number,
  body: string,
): Promise<string> {
  const key = await crypto.subtle.importKey(
    'raw',
    fromBase64(secret.replace(SECRET_PREFIX, '')),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  const signed = new TextEncoder().encode(`${msgId}.${timestamp}.${body}`)
  const digest = await crypto.subtle.sign('HMAC', key, signed)
  return `v1,${toBase64(new Uint8Array(digest))}`
}
