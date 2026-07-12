<template>
  <ToolViewHeader :title="fileName" />
  <div class="flex-1 min-h-0 w-full overflow-y-auto">
    <div dir="ltr" data-orientation="horizontal" class="flex flex-col min-h-0 h-full relative">
      <div
        class="flex-1 min-h-0 h-full text-sm flex flex-col py-0 outline-none overflow-auto"
      >
        <section class="flex relative w-full h-full" style="text-align: initial">
          <MonacoEditor
            :value="fileContent"
            :filename="fileName"
            :read-only="true"
            theme="vs"
            :line-numbers="'off'"
            :word-wrap="'on'"
            :minimap="false"
            :scroll-beyond-last-line="false"
            :automatic-layout="true"
          />
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, toRef } from "vue";
import { ToolContent } from "@/types/message";
import { viewFile } from "@/api/agent";
import MonacoEditor from "@/components/ui/MonacoEditor.vue";
import ToolViewHeader from "./ToolViewHeader.vue";
import { useLiveToolContent } from "@/composables/useLiveToolContent";

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

const fileContent = ref("");

const filePath = computed(() => {
  if (props.toolContent && props.toolContent.args.file) {
    return props.toolContent.args.file;
  }
  return "";
});

const fileName = computed(() => {
  if (filePath.value) {
    return filePath.value.split("/").pop() || "";
  }
  return "";
});

// Load file content
const loadFileContent = async () => {
  if (!props.live) {
    fileContent.value = props.toolContent.content?.content || "";
    return;
  }

  if (!filePath.value) return;

  try {
    const response = await viewFile(props.sessionId, filePath.value);
    fileContent.value = response.content;
  } catch (error) {
    console.error("Failed to load file content:", error);
  }
};

useLiveToolContent({
  toolContent: toRef(props, "toolContent"),
  live: toRef(props, "live"),
  targetKey: filePath,
  load: loadFileContent,
});
</script>
