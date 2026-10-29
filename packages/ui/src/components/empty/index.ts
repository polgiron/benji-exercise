import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export { default as EmptyContent } from './empty-content.vue'
export { default as EmptyDescription } from './empty-description.vue'
export { default as EmptyHeader } from './empty-header.vue'
export { default as EmptyMedia } from './empty-media.vue'
export { default as EmptyTitle } from './empty-title.vue'
export { default as Empty } from './empty.vue'

const GLOW =
  "relative size-14 rounded-2xl border bg-card shadow-card [&_svg:not([class*='size-'])]:size-6 before:absolute before:-inset-6 before:-z-10 before:rounded-full before:blur-2xl after:absolute after:-inset-20 after:-z-20 after:bg-dots after:[mask-image:radial-gradient(closest-side,black,transparent)]"

export const emptyMediaVariants = cva(
  'mb-2 flex shrink-0 items-center justify-center [&_svg]:pointer-events-none [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default: 'bg-transparent',
        icon: "bg-muted text-foreground flex size-10 shrink-0 items-center justify-center rounded-lg [&_svg:not([class*='size-'])]:size-6",
        // An icon tile lifted off a soft brand glow and a fading dot grid. The pseudo-elements sit
        // behind the tile; `Empty` is `isolate`, so they stay above the surrounding card.
        glow: `${GLOW} text-primary before:bg-primary/20`,
        // Same, for a failed load.
        danger: `${GLOW} text-destructive-foreground before:bg-destructive/20`,
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export type EmptyMediaVariants = VariantProps<typeof emptyMediaVariants>
