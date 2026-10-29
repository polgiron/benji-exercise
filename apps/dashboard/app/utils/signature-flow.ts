/** The stories the "How it works" diagram can tell, one tab each. */
export enum EFlowScenario {
  VALID = 'valid',
  TAMPERED = 'tampered',
  REPLAYED = 'replayed',
}

export enum EFlowNode {
  BENJI = 'benji',
  ATTACKER = 'attacker',
  RECEIVER = 'receiver',
}

/** The part of the request a step is about, lit up in the request view. */
export enum ERequestPart {
  BODY = 'body',
  ID = 'id',
  TIMESTAMP = 'timestamp',
  SIGNATURE = 'signature',
}

/** What the request on the wire is, as far as the receiver will be concerned. */
export enum EPacketState {
  UNSIGNED = 'unsigned',
  SIGNED = 'signed',
  TAMPERED = 'tampered',
  STALE = 'stale',
}

export enum EFlowVerdict {
  ACCEPTED = 'accepted',
  REJECTED = 'rejected',
}

export interface IFlowStep {
  title: string
  text: string
  /** Where the request sits; the node in the spotlight. */
  at: EFlowNode
  packet: EPacketState
  focus: ERequestPart[]
  verdict?: EFlowVerdict
  /** The receiver's answer, once it has one. */
  response?: string
}

export const FLOW_SCENARIO_LABELS: Record<EFlowScenario, string> = {
  [EFlowScenario.VALID]: 'Valid delivery',
  [EFlowScenario.TAMPERED]: 'Tampered payload',
  [EFlowScenario.REPLAYED]: 'Replayed request',
}

// The demo request. The secret is made up for this page; real ones are generated per endpoint.
export const DEMO_SECRET = 'whsec_MfKQ9r8GKYqrTwjUPD8ILPZIo2LaLaSw'
export const DEMO_DELIVERY_ID = 'dlv_Xq3vR8kLm2Pz7bNw'
export const DEMO_TIMESTAMP = 1793264400 // 2026-10-29 09:00:00 UTC
/** How late the replayed copy arrives: well past the 5 minute tolerance. */
export const REPLAY_DELAY_SECONDS = 2 * 60 * 60
export const TOLERANCE_SECONDS = 300
/** The canonical JSON the API sends: sorted keys, no spaces. */
export const DEMO_BODY =
  '{"created_at":"2026-10-29T09:00:00Z","data":{"kind":"earn","member_id":"mem_42","points":50},"id":"evt_8sKq2mWx","type":"reward_transaction_created"}'
export const TAMPERED_BODY = DEMO_BODY.replace('"points":50', '"points":5000')

const signStep: IFlowStep = {
  title: 'Benji signs the request',
  text: 'HMAC-SHA256 over "id.timestamp.body", keyed with the endpoint’s secret. The secret itself never travels: only the signature does.',
  at: EFlowNode.BENJI,
  packet: EPacketState.SIGNED,
  focus: [ERequestPart.ID, ERequestPart.TIMESTAMP, ERequestPart.BODY, ERequestPart.SIGNATURE],
}

export const FLOW_SCENARIOS: Record<EFlowScenario, IFlowStep[]> = {
  [EFlowScenario.VALID]: [
    {
      title: 'An event is queued',
      text: 'Your service posts an event. Benji stores it with one delivery per subscribed endpoint, in the same transaction, before anything is sent.',
      at: EFlowNode.BENJI,
      packet: EPacketState.UNSIGNED,
      focus: [ERequestPart.BODY],
    },
    signStep,
    {
      title: 'It travels over HTTPS',
      text: 'The raw body goes out with three headers: webhook-id, webhook-timestamp and webhook-signature. Anyone on the path can read them, nobody can forge them.',
      at: EFlowNode.ATTACKER,
      packet: EPacketState.SIGNED,
      focus: [ERequestPart.ID, ERequestPart.TIMESTAMP, ERequestPart.SIGNATURE],
    },
    {
      title: 'The receiver checks freshness',
      text: 'A timestamp more than 5 minutes away from the receiver’s clock is refused before anything else.',
      at: EFlowNode.RECEIVER,
      packet: EPacketState.SIGNED,
      focus: [ERequestPart.TIMESTAMP],
    },
    {
      title: 'Signatures match: accepted',
      text: 'The receiver signs the bytes it got with its copy of the secret and compares in constant time. Same bytes, same secret, same signature: it answers 2xx and dedupes on webhook-id.',
      at: EFlowNode.RECEIVER,
      packet: EPacketState.SIGNED,
      focus: [ERequestPart.SIGNATURE],
      verdict: EFlowVerdict.ACCEPTED,
      response: '200 received',
    },
  ],
  [EFlowScenario.TAMPERED]: [
    signStep,
    {
      title: 'Someone edits it on the way',
      text: 'A proxy or an attacker in the middle bumps the points from 50 to 5000. Without the secret they can’t sign the new body, so the old signature rides along.',
      at: EFlowNode.ATTACKER,
      packet: EPacketState.TAMPERED,
      focus: [ERequestPart.BODY],
    },
    {
      title: 'Signatures differ: rejected',
      text: 'The receiver signs the body it got and finds a different signature. It answers 401, and Benji marks the delivery failed instead of retrying a request the receiver refused.',
      at: EFlowNode.RECEIVER,
      packet: EPacketState.TAMPERED,
      focus: [ERequestPart.BODY, ERequestPart.SIGNATURE],
      verdict: EFlowVerdict.REJECTED,
      response: '401 invalid signature: no matching signature',
    },
  ],
  [EFlowScenario.REPLAYED]: [
    signStep,
    {
      title: 'Someone keeps a copy',
      text: 'The request is delivered and accepted. Whoever captured it on the way now holds a perfectly signed request.',
      at: EFlowNode.ATTACKER,
      packet: EPacketState.SIGNED,
      focus: [ERequestPart.SIGNATURE],
    },
    {
      title: 'Two hours later, they send it again',
      text: 'The copy is byte-for-byte genuine, but the timestamp is part of the signed content: it can’t be refreshed without breaking the signature.',
      at: EFlowNode.RECEIVER,
      packet: EPacketState.STALE,
      focus: [ERequestPart.TIMESTAMP],
    },
    {
      title: 'Too old: rejected',
      text: 'Two hours is far past the 5 minute tolerance, so the receiver refuses it before checking the signature. Within the window, webhook-id dedupe catches the copy.',
      at: EFlowNode.RECEIVER,
      packet: EPacketState.STALE,
      focus: [ERequestPart.TIMESTAMP],
      verdict: EFlowVerdict.REJECTED,
      response: '401 invalid signature: timestamp outside tolerance',
    },
  ],
}

const SCENARIOS = new Set<string>(Object.values(EFlowScenario))

export function isFlowScenario(value: unknown): value is EFlowScenario {
  return typeof value === 'string' && SCENARIOS.has(value)
}
