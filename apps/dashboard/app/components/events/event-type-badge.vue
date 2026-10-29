<script setup lang="ts">
import { Gift, Link2, Megaphone, Zap } from '@lucide/vue'
import { Badge, cn } from '@repo/ui'
import type { Component, HTMLAttributes } from 'vue'
import { EEventType } from '~/api/types'
import { isEventType } from '~/utils/event-types'

interface Props {
  type: string
  class?: HTMLAttributes['class']
}

const props = defineProps<Props>()

// One color and icon per type, wherever it shows, from the theme's `event-*` tokens.
const STYLES: Record<EEventType, { icon: Component; class: string }> = {
  [EEventType.CAMPAIGN_UPDATED]: {
    icon: Megaphone,
    class: 'border-event-campaign/25 bg-event-campaign/10 text-event-campaign-foreground',
  },
  [EEventType.MEMBER_ACCOUNT_LINKED]: {
    icon: Link2,
    class: 'border-event-member/25 bg-event-member/10 text-event-member-foreground',
  },
  [EEventType.REWARD_TRANSACTION_CREATED]: {
    icon: Gift,
    class: 'border-event-reward/25 bg-event-reward/10 text-event-reward-foreground',
  },
}

// A type the dashboard doesn't know yet keeps the neutral code look.
const style = computed(() =>
  isEventType(props.type) ? STYLES[props.type] : { icon: Zap, class: 'border-border' },
)
</script>

<template>
  <Badge variant="code" :class="cn(style.class, props.class)">
    <component :is="style.icon" />
    {{ type }}
  </Badge>
</template>
