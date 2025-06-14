<template>
  <div
    class="h-[36px] flex items-center px-3 w-full bg-[var(--background-gray-main)] border-b border-[var(--border-main)] rounded-t-[12px] shadow-[inset_0px_1px_0px_0px_#FFFFFF] dark:shadow-[inset_0px_1px_0px_0px_#FFFFFF30]">
    <div class="flex-1 flex items-center justify-center">
      <div class="max-w-[250px] truncate text-[var(--text-tertiary)] text-sm font-medium text-center">
      Search
      </div>
    </div>
  </div>
  <div class="flex-1 min-h-0 w-full overflow-y-auto">
    <div class="flex-1 min-h-0 max-w-[640] mx-auto">
      <div class="flex flex-col overflow-auto h-full px-4 py-3">
        <div v-for="result in toolContent.content?.results" class="py-3 pt-0 border-b border-[var(--border-light)]">
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
import { ToolContent } from '../types/message';

defineProps<{
  sessionId: string;
  toolContent: ToolContent;
  live: boolean;
}>();

</script>
