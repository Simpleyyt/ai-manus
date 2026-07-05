<template>
  <ToolViewHeader :title="shellSessionId" />
  <div class="flex-1 min-h-0 w-full overflow-y-auto">
    <div dir="ltr" data-orientation="horizontal" class="flex flex-col flex-1 min-h-0">
      <div
        class="py-2 flex-1 font-mono text-sm leading-relaxed px-3 outline-none overflow-auto whitespace-pre-wrap break-all">
        <code v-html="shell"></code>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, toRef } from 'vue';
import { viewShellSession } from '@/api/agent';
import { ToolContent } from '@/types/message';
import ToolViewHeader from './ToolViewHeader.vue';
import { useLiveToolContent } from '@/composables/useLiveToolContent';

const props = defineProps<{
  sessionId: string;
  toolContent: ToolContent;
  live: boolean;
}>();

defineExpose({
  loadContent: () => {
    loadShellContent();
  }
});

const shell = ref('');

// Get shellSessionId from toolContent
const shellSessionId = computed(() => {
  if (props.toolContent && props.toolContent.args.id) {
    return props.toolContent.args.id;
  }
  return '';
});

const updateShellContent = (console: any) => {
  if (!console) return;
  let newShell = '';
  for (const e of console) {
    newShell += `<span style="color: rgb(0, 187, 0);">${e.ps1}</span><span> ${e.command}</span>\n`;
    newShell += `<span>${e.output}</span>\n`;
  }
  if (newShell !== shell.value) {
    shell.value = newShell;
  }
}

// Function to load Shell session content
const loadShellContent = async () => {
  if (!props.live) {
    updateShellContent(props.toolContent.content?.console);
    return;
  }

  if (!shellSessionId.value) return;

  try {
    const response = await viewShellSession(props.sessionId, shellSessionId.value);
    updateShellContent(response.console);
  } catch (error) {
    console.error("Failed to load shell content:", error);
  }
};

useLiveToolContent({
  toolContent: toRef(props, 'toolContent'),
  live: toRef(props, 'live'),
  targetKey: shellSessionId,
  load: loadShellContent,
});
</script>
