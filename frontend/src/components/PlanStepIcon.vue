<template>
  <Check
    v-if="status === 'completed'"
    :size="12"
    class="shrink-0"
    color="var(--function-success)" />
  <Clock
    v-else-if="status === 'pending'"
    :size="12"
    class="shrink-0"
    color="var(--icon-tertiary)" />
  <Loader2
    v-else-if="status === 'running'"
    :size="12"
    class="shrink-0 animate-spin text-[var(--icon-brand)]" />
  <span
    v-else
    class="mx-[1.5px] size-[9px] shrink-0 rotate-[30deg] rounded-[3px] bg-[var(--text-brand)] shadow-[0_0_3px_0_var(--text-brand)]" />
</template>

<script setup lang="ts">
import { Check, Clock, Loader2 } from 'lucide-vue-next';
import type { StepEventData } from '../types/event';

defineProps<{
  status: StepEventData['status'];
}>();
</script>
