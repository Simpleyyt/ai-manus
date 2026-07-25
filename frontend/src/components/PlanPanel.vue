<template>
  <!-- ManusComputerPlanner — lives under Computer timeline -->
  <button
    v-if="plan?.steps?.length"
    type="button"
    class="clickable flex w-full flex-col p-[16px] pe-0 text-start hover:bg-[var(--fill-tsp-gray-main)] shrink-0 border-0 bg-transparent cursor-pointer"
    :class="{ 'gap-[8px]': isExpanded }"
    :aria-label="isExpanded ? t('Collapse task progress') : t('Expand task progress')"
    :aria-expanded="isExpanded"
    @click="togglePanel">
    <div class="flex w-full items-center justify-between gap-[12px] pe-[16px]">
      <span
        v-if="isExpanded"
        class="shrink-0 text-sm font-[500] text-[var(--text-primary)]">
        {{ t('Task progress') }}
      </span>
      <div v-else class="relative min-w-0 flex-1 overflow-hidden">
        <div class="flex min-w-0 items-center gap-[8px]">
          <PlanStepIcon :status="currentStepStatus" />
          <span
            class="min-w-0 truncate text-sm text-[var(--text-primary)]"
            :title="currentStepTitle">
            {{ currentStepTitle }}
          </span>
        </div>
      </div>
      <span class="flex shrink-0 items-center justify-center gap-[4px]">
        <span class="text-xs text-[var(--text-tertiary)]">{{ planProgress }}</span>
        <ChevronUp v-if="isExpanded" :size="16" class="text-[var(--icon-tertiary)]" />
        <ChevronDown v-else :size="16" class="text-[var(--icon-tertiary)]" />
      </span>
    </div>

    <div
      v-if="isExpanded"
      class="flex max-h-[260px] w-full flex-col items-start gap-[4px] overflow-y-auto overscroll-contain pe-[16px]">
      <div
        v-for="step in plan.steps"
        :key="step.id"
        class="flex min-h-[20px] min-w-0 max-w-full items-center gap-[8px]">
        <PlanStepIcon :status="step.status" />
        <span
          class="min-w-0 truncate text-sm text-[var(--text-primary)]"
          :title="step.description">
          {{ step.description }}
        </span>
      </div>
    </div>
  </button>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { ChevronUp, ChevronDown } from 'lucide-vue-next';
import PlanStepIcon from './PlanStepIcon.vue';
import type { PlanEventData, StepEventData } from '../types/event';

const props = defineProps<{
  plan: PlanEventData;
}>();

const { t } = useI18n();
const isExpanded = ref(false);

const togglePanel = () => {
  isExpanded.value = !isExpanded.value;
};

const steps = computed(() => props.plan?.steps ?? []);

const currentIndex = computed(() => {
  const list = steps.value;
  if (!list.length) return 0;
  let lastDone = -1;
  for (let i = 0; i < list.length; i++) {
    if (list[i].status === 'completed') lastDone = i;
  }
  return Math.min(list.length - 1, lastDone + 1);
});

const planProgress = computed(() => `${currentIndex.value + 1} / ${steps.value.length || 1}`);

const currentStep = computed((): StepEventData | undefined => steps.value[currentIndex.value]);

const currentStepTitle = computed(() => {
  if (!currentStep.value) return t('Task Completed');
  if (steps.value.every((s) => s.status === 'completed')) return t('Task Completed');
  return currentStep.value.description;
});

const currentStepStatus = computed(() => {
  if (steps.value.every((s) => s.status === 'completed')) return 'completed' as const;
  return currentStep.value?.status ?? 'pending';
});
</script>
