import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export { default as StatusDot } from './status-dot.vue'

export const statusDotVariants = cva('inline-block size-2 shrink-0 rounded-full', {
  variants: {
    tone: {
      success: 'bg-success',
      warning: 'bg-warning',
      danger: 'bg-destructive',
      info: 'bg-info',
      muted: 'bg-muted-foreground',
    },
    pulse: {
      // A ring of the dot's own color ripples out of it: something live is happening.
      true: 'relative after:absolute after:inset-0 after:animate-ping after:rounded-full after:bg-inherit motion-reduce:after:hidden',
      false: '',
    },
  },
  defaultVariants: {
    tone: 'muted',
    pulse: false,
  },
})
export type StatusDotVariants = VariantProps<typeof statusDotVariants>
