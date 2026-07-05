<template>
  <ToolViewHeader title="Search" />
  <div class="flex-1 min-h-0 w-full overflow-y-auto">
    <div class="flex-1 min-h-0 max-w-[640px] mx-auto">
      <div class="flex flex-col overflow-auto h-full px-4 py-3">
        <div v-for="result in toolContent.content?.results" :key="result.link"
          class="py-3 pt-0 border-b border-[var(--border-light)]">
          <a :href="result.link" target="_blank"
            class="block text-[var(--text-primary)] text-sm font-medium hover:underline line-clamp-2 cursor-pointer">
            {{ result.title }}
          </a>
          <div class="text-[var(--text-tertiary)] text-xs mt-0.5 line-clamp-3">{{ result.snippet }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ToolContent } from '@/types/message';
import ToolViewHeader from './ToolViewHeader.vue';

defineProps<{
  sessionId: string;
  toolContent: ToolContent;
  live: boolean;
}>();
</script>
