<script setup lang="ts">
import { Clock, CopyCheck, FileLock, Fingerprint } from '@lucide/vue'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CodeBlock,
  IconTile,
  PageHeader,
} from '@repo/ui'

const guarantees = [
  {
    icon: Fingerprint,
    title: 'It comes from Benji',
    text: 'Only Benji and your endpoint hold the secret, so only Benji can produce a signature your endpoint accepts.',
  },
  {
    icon: FileLock,
    title: 'Nobody changed it',
    text: 'The signature covers the raw body byte for byte: edit one character and it no longer matches.',
  },
  {
    icon: Clock,
    title: 'It was sent just now',
    text: 'The timestamp is signed too. Anything older than 5 minutes is refused, so a captured request goes stale.',
  },
  {
    icon: CopyCheck,
    title: 'It counts once',
    text: 'Retries and replays keep the same webhook-id: dedupe on it, and a delivery seen twice is handled once.',
  },
]

const SNIPPET = `from app.signing import InvalidSignature, verify

@app.post("/webhooks")
async def receive(request: Request) -> Response:
    body = await request.body()  # the raw bytes: parsing and re-encoding JSON changes them
    try:
        verify(SECRET, request.headers, body)  # freshness first, then the HMAC
    except InvalidSignature as exc:
        return Response(f"invalid signature: {exc}", status_code=401)
    if already_seen(request.headers["webhook-id"]):
        return Response(status_code=200)  # a retry of something we handled
    ...`
</script>

<template>
  <section class="space-y-6">
    <PageHeader
      title="How it works"
      description="How every delivery proves to your endpoint that it came from Benji, untouched and on time."
      class="motion-safe:animate-rise"
    />

    <SignatureFlow class="motion-safe:animate-rise motion-safe:[animation-delay:60ms]" />

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Card
        v-for="(guarantee, index) in guarantees"
        :key="guarantee.title"
        class="gap-3 px-5 motion-safe:animate-rise"
        :style="{ animationDelay: `${120 + index * 50}ms` }"
      >
        <IconTile class="size-9 [&_svg]:size-5"><component :is="guarantee.icon" /></IconTile>
        <p class="text-sm font-semibold">{{ guarantee.title }}</p>
        <p class="text-xs text-muted-foreground">{{ guarantee.text }}</p>
      </Card>
    </div>

    <Card class="motion-safe:animate-rise motion-safe:[animation-delay:320ms]">
      <CardHeader>
        <CardTitle>Verify on your side</CardTitle>
        <CardDescription>
          Benji follows Standard Webhooks, so any of its verifier libraries works. This is the API's
          own <code class="font-mono">verify()</code>, the one the mock receivers use.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <CodeBlock surface="muted">{{ SNIPPET }}</CodeBlock>
      </CardContent>
    </Card>
  </section>
</template>
