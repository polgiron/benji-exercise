<script setup lang="ts">
import { RotateCcw, TriangleAlert } from '@lucide/vue'
import {
  Button,
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '@repo/ui'

interface Props {
  message?: string
}

defineProps<Props>()
defineEmits<{ retry: [] }>()
</script>

<template>
  <!-- A query that failed: what went wrong (the ApiError's message) and a way to try again. -->
  <Empty class="p-4 md:p-8">
    <EmptyHeader>
      <EmptyMedia variant="danger"><TriangleAlert /></EmptyMedia>
      <EmptyTitle class="text-base">Couldn't load this</EmptyTitle>
      <EmptyDescription>{{ message ?? 'Something went wrong.' }}</EmptyDescription>
    </EmptyHeader>
    <EmptyContent>
      <!-- type="button": inside a form (the create-endpoint dialog) it must not submit it. -->
      <Button variant="outline" size="sm" type="button" @click="$emit('retry')">
        <RotateCcw /> Try again
      </Button>
    </EmptyContent>
  </Empty>
</template>
