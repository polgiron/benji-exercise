import type { components } from './schema'

type Schemas = components['schemas']

export type IEventType = Schemas['EventTypeOut']
export type IEndpoint = Schemas['EndpointOut']
export type IEndpointCreated = Schemas['EndpointCreated']
export type IEndpointCreate = Schemas['EndpointCreate']
export type IEndpointUpdate = Schemas['EndpointUpdate']
export type IEventCreate = Schemas['EventCreate']
export type IEventPublished = Schemas['EventPublished']
export type IDeliverySummary = Schemas['DeliverySummary']
export type IDeliveryDetail = Schemas['DeliveryDetail']
export type IDeliveryStats = Schemas['DeliveryStats']
export type IAttempt = Schemas['AttemptOut']
export type IDeliveryActivity = Schemas['DeliveryActivity']
export type IActivityBucket = Schemas['ActivityBucket']
export type IDemoSeeded = Schemas['DemoSeeded']

// Same strings as the API's StrEnums. The schema types `status` and `trigger` as plain
// strings on the summary (see docs/DASHBOARD_PLAN.md "Contract nits"), so these are the
// names the UI switches on.
export enum EDeliveryStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  SUCCEEDED = 'succeeded',
  FAILED = 'failed',
}

// The API's registered event types (GET /api/event-types). The registry can grow ahead of the
// dashboard: a key outside this enum still renders, with a neutral badge.
export enum EEventType {
  CAMPAIGN_UPDATED = 'campaign_updated',
  MEMBER_ACCOUNT_LINKED = 'member_account_linked',
  REWARD_TRANSACTION_CREATED = 'reward_transaction_created',
}

export enum EAttemptTrigger {
  AUTO = 'auto',
  REPLAY = 'replay',
}

/** The API's ActivityRange: how far back the activity chart looks. */
export enum EActivityRange {
  DAY = '24h',
  WEEK = '7d',
  MONTH = '30d',
}

export interface IDeliveryFilters {
  status?: EDeliveryStatus
  endpointId?: string
  eventType?: string
  limit?: number
}
