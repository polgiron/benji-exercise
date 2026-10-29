import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export { default as CodeBlock } from './CodeBlock.vue'

/** Monospace, preformatted text: JSON payloads and schemas, secrets. */
export const codeBlockVariants = cva(
  'overflow-auto rounded-input border font-mono whitespace-pre text-foreground',
  {
    variants: {
      surface: {
        card: 'bg-card',
        muted: 'bg-muted',
      },
      size: {
        default: 'p-3 text-code',
        sm: 'p-2 text-2xs',
        // One line that truncates rather than scrolls (an ID, a secret).
        line: 'px-3 py-2 text-xs truncate whitespace-nowrap',
      },
      height: {
        auto: '',
        sm: 'max-h-48',
        md: 'max-h-72',
      },
    },
    defaultVariants: {
      surface: 'card',
      size: 'default',
      height: 'auto',
    },
  },
)
export type CodeBlockVariants = VariantProps<typeof codeBlockVariants>
