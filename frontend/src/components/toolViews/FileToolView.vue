<template>
  <div dir="ltr" class="computer-monaco-panel flex flex-col min-h-0 h-full relative flex-1 w-full bg-[var(--background-gray-main)]">
    <div
      class="flex items-center justify-center px-[16px] py-[8px]"
      :class="{ hidden: !hasOldContent }">
      <div class="backdrop-blur-3xl inline-flex h-7 items-center rounded-lg bg-[var(--tab-fill)] p-0.5">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          class="inline-flex items-center justify-center rounded-md px-3 py-1 text-xs transition-colors text-[var(--text-tertiary)] hover:cursor-pointer data-[state=on]:bg-[var(--fill-white)] data-[state=on]:text-[var(--text-primary)] data-[state=on]:shadow-[0px_0px_2px_0px_var(--shadow-S)]"
          :data-state="activeTab === tab.value ? 'on' : 'off'"
          @click="activeTab = tab.value">
          {{ tab.label }}
        </button>
      </div>
    </div>

    <div class="focus-visible:outline-none flex-1 min-h-0 h-full text-sm flex flex-col py-0 outline-none overflow-auto">
      <div v-if="activeView === 'diff' && hasOldContent" class="flex-1 min-h-0 h-full">
        <MonacoDiffEditor
          class="w-full h-full"
          :original="oldContent || ''"
          :modified="fileContent"
          :filename="fileName"
          :theme="monacoTheme"
        />
      </div>
      <section
        v-else
        class="flex relative w-full h-full flex-1 min-h-0"
        style="text-align: initial">
        <MonacoEditor
          :value="activeView === 'oldContent' ? (oldContent || '') : fileContent"
          :filename="fileName"
          :read-only="true"
          :theme="monacoTheme"
          :line-numbers="'off'"
          :word-wrap="'on'"
          :minimap="false"
          :scroll-beyond-last-line="false"
          :automatic-layout="true"
        />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, toRef, watch, onMounted, onBeforeUnmount } from 'vue';
import { useI18n } from 'vue-i18n';
import { ToolContent } from '@/types/message';
import { viewFile } from '@/api/agent';
import MonacoEditor from '@/components/ui/MonacoEditor.vue';
import MonacoDiffEditor from '@/components/ui/MonacoDiffEditor.vue';
import { useLiveToolContent } from '@/composables/useLiveToolContent';
import { useDocumentDark } from '@/composables/useDocumentDark';
import { eventBus } from '@/utils/eventBus';

type FileTab = 'diff' | 'oldContent' | 'newContent';

const props = defineProps<{
  sessionId: string;
  toolContent: ToolContent;
  live: boolean;
}>();

defineExpose({
  loadContent: () => {
    loadFileContent();
  },
});

const { t } = useI18n();
const isDark = useDocumentDark();
/** Panel bg is --background-gray-main; pair with vs-dark so tokens aren't light-on-dark mess */
const monacoTheme = computed(() => (isDark.value ? 'vs-dark' : 'vs'));
const fileContent = ref('');
const oldContent = ref<string | null>(null);
/** Official default selected tab is Modified / 已修改 */
const activeTab = ref<FileTab>('newContent');

const tabs = computed(() => [
  { label: t('Diff'), value: 'diff' as const },
  { label: t('Original'), value: 'oldContent' as const },
  { label: t('Modified'), value: 'newContent' as const },
]);

const hasOldContent = computed(() => oldContent.value != null);

const activeView = computed<FileTab>(() => {
  if (!hasOldContent.value) return 'newContent';
  return activeTab.value;
});

const filePath = computed(() => {
  if (props.toolContent && props.toolContent.args.file) {
    return props.toolContent.args.file;
  }
  return '';
});

const fileName = computed(() => {
  if (filePath.value) {
    return filePath.value.split('/').pop() || '';
  }
  return '';
});

const applyContentPayload = () => {
  const payload = props.toolContent.content;
  if (!props.live) {
    fileContent.value = payload?.content || '';
  }
  if (payload && 'old_content' in payload) {
    oldContent.value = payload.old_content ?? '';
  } else if (!props.live) {
    oldContent.value = null;
  }
};

const loadFileContent = async () => {
  applyContentPayload();

  if (!props.live) {
    return;
  }

  if (!filePath.value) return;

  try {
    const response = await viewFile(props.sessionId, filePath.value);
    fileContent.value = response.content;
    if (props.toolContent.content && 'old_content' in props.toolContent.content) {
      oldContent.value = props.toolContent.content.old_content ?? '';
    }
  } catch (error) {
    console.error('Failed to load file content:', error);
  }
};

watch(
  () => props.toolContent.content,
  () => {
    applyContentPayload();
  },
  { immediate: true, deep: true },
);

useLiveToolContent({
  toolContent: toRef(props, 'toolContent'),
  live: toRef(props, 'live'),
  targetKey: filePath,
  load: loadFileContent,
  // Official: file_update over WS — no 5s REST poll
  pushOnly: true,
});

const onFileUpdate = (payload: {
  sessionId: string
  path: string
  content: string
  oldContent?: string | null
}) => {
  if (payload.sessionId !== props.sessionId) return
  if (!filePath.value || payload.path !== filePath.value) return
  fileContent.value = payload.content
  if (payload.oldContent !== undefined) {
    oldContent.value = payload.oldContent ?? ''
  }
}

onMounted(() => {
  eventBus.on('tool:file_update', onFileUpdate)
})

onBeforeUnmount(() => {
  eventBus.off('tool:file_update', onFileUpdate)
})
</script>
