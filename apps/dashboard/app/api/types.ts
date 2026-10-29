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

// Same strings as the API's StrEnums. The schema types `status` and `trigger` as plain
// strings on the summary (see docs/DASHBOARD_PLAN.md "Contract nits"), so these are the
// names the UI switches on.
export enum EDeliveryStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  SUCCEEDED = 'succeeded',
  FAILED = 'failed',
}

export enum EAttemptTrigger {
  AUTO = 'auto',
  REPLAY = 'replay',
}

export interface IDeliveryFilters {
  status?: EDeliveryStatus
  endpointId?: string
  limit?: number
}
