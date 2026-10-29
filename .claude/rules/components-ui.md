---
paths:
  - 'apps/dashboard/app/**/*.vue'
  - 'packages/ui/**'
---

# Components and `@repo/ui`

### Components

- One component per `.vue` file, named in kebab-case; Nuxt turns it into the PascalCase tag
  (`delivery-timeline.vue` → `<DeliveryTimeline />`). Don't stack a `Foo` and a `FooRow` in one
  file through render functions — split into siblings.
- `<script setup lang="ts">`, with props typed through `defineProps<Props>()` and an `interface Props`
  in the same file. Only **shared** shapes leave the component.
- A feature that grows past a couple of files gets its folder under `app/components/<feature>/`.
  Logic shared between components goes in a composable (`app/composables/use-*.ts`); pure helpers with
  no Vue in them go in `@repo/utils` or a `utils/` file.
- No barrel `index.ts` that only re-exports siblings in the dashboard — Nuxt auto-imports components
  and composables. `packages/ui` is the exception: each shadcn-vue component folder keeps its
  generated `index.ts`, and `packages/ui/src/index.ts` re-exports them.
- Conditional rendering: `v-if` when both branches render (`v-if` / `v-else`), `v-show` only for
  something toggled often. Guard a count with `count > 0`, not a bare `count`.
- Inline values referenced only once instead of naming them, unless the name documents non-obvious
  intent or the expression is long or repeated.

### UI (`@repo/ui`)

- Compose from existing `@repo/ui` exports before writing new markup or pulling in another component
  library. If a primitive is missing, **add it to `@repo/ui`** (`pnpm dlx shadcn-vue@latest add <name>`
  from `packages/ui`, rename its files to kebab-case — shadcn-vue writes PascalCase — then export
  it from `src/index.ts`) rather than inlining a one-off in the app.
- Colours, radii and spacing come from the tokens in `packages/ui/src/styles/` — never a hex value or
  an arbitrary Tailwind colour in the app. Both the light and the dark theme must still read.
- Don't put `size-*` / `w-*` / `h-*` on icons inside a `Button`: its variants size them. Non-size
  classes on icons (`text-destructive`) are fine.
- Class names go through `cn` from `@repo/ui`, not string concatenation or template literals.
  **Conditional classes use the object form** — `cn('rounded-md', { 'opacity-50': !endpoint.enabled })`
  — not `cn(foo && 'bar')`. In templates, Vue's `:class="{ … }"` object form is fine too.
