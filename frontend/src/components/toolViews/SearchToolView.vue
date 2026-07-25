<template>
  <div class="flex-1 min-h-0 flex flex-col overflow-auto h-full px-4 py-3">
    <div
      v-for="(result, index) in results"
      :key="result.link"
      class="py-3"
      :class="{
        'pt-0': index === 0,
        'pb-0': index === results.length - 1,
        'border-b border-[var(--border-light)]': index !== results.length - 1,
      }">
      <a
        :href="result.link"
        target="_blank"
        rel="noreferrer"
        class="block text-[var(--text-primary)] text-sm font-medium hover:underline line-clamp-2 cursor-pointer">
        <img
          :src="faviconUrl(result.link)"
          width="16"
          height="16"
          alt=""
          class="float-left mr-2 mt-0.5 rounded-full border"
        >
        {{ result.title }}
      </a>
      <div class="text-[var(--text-tertiary)] text-xs mt-0.5 line-clamp-3">{{ result.snippet }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ToolContent } from '@/types/message';

const props = defineProps<{
  sessionId: string;
  toolContent: ToolContent;
  live: boolean;
}>();

const results = computed(() => {
  const list = props.toolContent.content?.results || [];
  return list.filter((r: { link?: string }) => !!r.link);
});

const faviconUrl = (link: string) =>
  `https://s2.googleusercontent.com/s2/favicons?domain=${encodeURIComponent(link)}&sz=32`;
</script>
