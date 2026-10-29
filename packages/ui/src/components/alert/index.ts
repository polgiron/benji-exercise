import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export { default as Alert } from './Alert.vue'
export { default as AlertDescription } from './AlertDescription.vue'
export { default as AlertTitle } from './AlertTitle.vue'

// shadcn-vue's alert, with the status tones the dashboard reports in: a tint of the status
// colour behind its `-foreground` text, the same pairing as the status badges.
export const alertVariants = cva(
  'relative w-full rounded-card border px-4 py-3 text-sm grid has-[>svg]:grid-cols-[calc(var(--spacing)*4)_1fr] grid-cols-[0_1fr] has-[>svg]:gap-x-3 gap-y-0.5 items-start [&>svg]:size-4 [&>svg]:translate-y-0.5 [&>svg]:text-current',
  {
    variants: {
      variant: {
        default: 'bg-card text-card-foreground',
        destructive: 'border-transparent bg-destructive/10 text-destructive-foreground',
        success: 'border-transparent bg-success/10 text-success-foreground',
        info: 'border-transparent bg-info/10 text-info-foreground',
        warning: 'border-transparent bg-warning/10 text-warning-foreground',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)
export type AlertVariants = VariantProps<typeof alertVariants>
