import { createSharedComposable, useLocalStorage } from '@vueuse/core'

/** Whether the test panel shows. Remembered per browser: it's a viewer's preference. */
export const useTestPanel = createSharedComposable(() =>
  useLocalStorage('benji:test-panel-open', true),
)
