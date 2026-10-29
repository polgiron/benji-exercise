import { createSharedComposable, useIntervalFn, useNow as useTickingNow } from '@vueuse/core'

/** One clock ticking every second, shared by every countdown and "updated 3 s ago". */
export const useNow = createSharedComposable(() =>
  // The default ticks every animation frame: far more than a seconds countdown needs.
  useTickingNow({ scheduler: (tick) => useIntervalFn(tick, 1000) }),
)
