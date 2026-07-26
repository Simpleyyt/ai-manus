<template>
  <!-- Official waiting footer: TaskWaitingIcon + "{product} will continue after your reply" + Copy -->
  <div v-if="visible" class="flex items-center gap-[12px] mt-1">
    <div class="flex items-center gap-[8px] pe-[8px] text-[var(--function-warning)] text-sm">
      <svg
        height="16"
        width="16"
        fill="none"
        viewBox="0 0 16 16"
        xmlns="http://www.w3.org/2000/svg"
        class="flex-shrink-0"
        aria-hidden="true">
        <circle
          cx="8"
          cy="8"
          r="6.5"
          stroke="currentColor"
          stroke-dasharray="2.44 1.62"
          stroke-width="1.5" />
      </svg>
      {{ t('{product} will continue after your reply', { product: productName }) }}
    </div>
    <template v-if="copyText.trim()">
      <div class="w-px h-[18px] bg-[var(--border-dark)] flex-shrink-0" />
      <ChatMessageCopyButton :text="copyText" button-class="size-[28px]" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import ChatMessageCopyButton from './ChatMessageCopyButton.vue';

defineProps<{
  visible: boolean;
  copyText: string;
}>();

const { t } = useI18n();
const productName = computed(() => 'Manus');
</script>
