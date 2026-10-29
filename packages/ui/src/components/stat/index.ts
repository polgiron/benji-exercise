import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export { default as Stat } from './Stat.vue'
export { default as StatGrid } from './StatGrid.vue'

/** A labelled count: one tile of a StatGrid. */
export const statValueVariants = cva('text-lg font-semibold tabular-nums', {
  variants: {
    tone: {
      default: '',
      danger: 'text-destructive-foreground',
    },
  },
  defaultVariants: {
    tone: 'default',
  },
})
export type StatValueVariants = VariantProps<typeof statValueVariants>
