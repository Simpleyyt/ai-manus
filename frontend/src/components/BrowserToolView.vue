<template>
  <div
    class="h-[36px] flex items-center px-3 w-full bg-[var(--background-gray-main)] border-b border-[var(--border-main)] rounded-t-[12px] shadow-[inset_0px_1px_0px_0px_#FFFFFF] dark:shadow-[inset_0px_1px_0px_0px_#FFFFFF30]">
    <div class="flex-1 flex items-center justify-center">
      <div class="max-w-[250px] truncate text-[var(--text-tertiary)] text-sm font-medium text-center">
        {{ toolContent?.args?.url || 'Browser' }}
      </div>
    </div>
    <div class="flex items-center gap-2">
      <button
        class="px-2 py-1 text-xs rounded transition-colors bg-[var(--text-brand)] text-white"
        disabled
        title="仅支持 Crawl4AI 快速模式">
        快速
      </button>
    </div>
  </div>
  <div class="flex-1 min-h-0 w-full overflow-y-auto">
    <div class="px-0 py-0 flex flex-col relative h-full">
      <div class="w-full h-full bg-[var(--fill-white)] relative">
        <div class="w-full h-full overflow-auto p-4">
          <div v-if="toolContent?.content?.content" 
               class="prose prose-sm max-w-none"
               v-html="renderedMarkdown">
          </div>
          <div v-else class="flex items-center justify-center h-full text-[var(--text-tertiary)]">
            暂无内容
          </div>
        </div>
        <div v-if="interactiveElements.length > 0" 
             class="absolute bottom-4 left-4 right-4 bg-[var(--background-white-main)] border border-[var(--border-main)] rounded-lg p-3 max-h-32 overflow-y-auto">
          <div class="text-xs font-medium text-[var(--text-secondary)] mb-2">可交互元素:</div>
          <div class="flex flex-wrap gap-1">
            <button
              v-for="element in interactiveElements"
              :key="element.index"
              @click="clickElement(element.index)"
              class="px-2 py-1 text-xs bg-[var(--fill-tsp-gray-main)] hover:bg-[var(--fill-tsp-white-dark)] rounded transition-colors"
              :title="`${element.tag}: ${element.text}`">
              {{ element.index }}: {{ element.text.substring(0, 20) }}{{ element.text.length > 20 ? '...' : '' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ToolContent } from '../types/message';
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const props = defineProps<{
  sessionId: string;
  toolContent: ToolContent;
  live: boolean;
}>();

const { t } = useI18n();

const toolContent = props.toolContent;

const renderedMarkdown = computed(() => {
  if (toolContent.content?.content) {
    const rawMarkdown = toolContent.content.content;
    const html = marked(rawMarkdown);
    return DOMPurify.sanitize(html);
  }
  return '';
});

const interactiveElements = computed(() => {
  if (toolContent.content?.interactive_elements) {
    return toolContent.content.interactive_elements;
  }
  return [];
});

const clickElement = (index: number) => {
  // 可根据需要实现交互逻辑
  console.log(`Clicked element ${index}`);
};
</script>

<style scoped>
.prose {
  color: var(--text-primary);
}

.prose h1, .prose h2, .prose h3, .prose h4, .prose h5, .prose h6 {
  color: var(--text-primary);
  font-weight: 600;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.prose p {
  margin-bottom: 1em;
  line-height: 1.6;
}

.prose a {
  color: var(--text-brand);
  text-decoration: underline;
}

.prose a:hover {
  text-decoration: none;
}

.prose ul, .prose ol {
  margin-left: 1.5em;
  margin-bottom: 1em;
}

.prose li {
  margin-bottom: 0.25em;
}

.prose code {
  background-color: var(--fill-tsp-gray-main);
  padding: 0.125em 0.25em;
  border-radius: 0.25em;
  font-size: 0.875em;
}

.prose pre {
  background-color: var(--fill-tsp-gray-main);
  padding: 1em;
  border-radius: 0.5em;
  overflow-x: auto;
  margin-bottom: 1em;
}

.prose blockquote {
  border-left: 4px solid var(--border-main);
  padding-left: 1em;
  margin-left: 0;
  color: var(--text-secondary);
}

.prose table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1em;
}

.prose th, .prose td {
  border: 1px solid var(--border-main);
  padding: 0.5em;
  text-align: left;
}

.prose th {
  background-color: var(--fill-tsp-gray-main);
  font-weight: 600;
}
</style>
