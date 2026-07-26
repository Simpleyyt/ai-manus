<template>
  <!-- Official TaskCompleted footer (an pill + Copy; Fork / survey skipped) -->
  <div v-if="visible" class="w-full flex flex-col gap-[16px] mt-1">
    <div class="flex items-center flex-wrap gap-[12px]">
      <div
        class="rounded-full text-[var(--function-success)] text-sm w-max max-w-full flex items-center gap-[8px] pe-[8px]">
        <Check :size="16" color="var(--function-success)" class="flex-shrink-0" />
        {{ t('Task completed') }}
      </div>
      <div
        v-if="copyText.trim()"
        class="w-px h-[18px] bg-[var(--border-dark)] flex-shrink-0" />
      <div v-if="copyText.trim()" class="flex items-center gap-[4px]">
        <ChatMessageCopyButton :text="copyText" button-class="size-[28px]" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { Check } from 'lucide-vue-next';
import ChatMessageCopyButton from './ChatMessageCopyButton.vue';

defineProps<{
  visible: boolean;
  copyText: string;
}>();

const { t } = useI18n();
</script>
