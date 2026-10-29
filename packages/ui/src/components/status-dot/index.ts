import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export { default as StatusDot } from './StatusDot.vue'

export const statusDotVariants = cva('inline-block size-2 shrink-0 rounded-full', {
  variants: {
    tone: {
      success: 'bg-success',
      warning: 'bg-warning',
      muted: 'bg-muted-foreground',
    },
    pulse: {
      true: 'animate-pulse',
      false: '',
    },
  },
  defaultVariants: {
    tone: 'muted',
    pulse: false,
  },
})
export type StatusDotVariants = VariantProps<typeof statusDotVariants>
