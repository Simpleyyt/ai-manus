<template>
  <div
    class="h-[36px] flex items-center px-3 w-full bg-[var(--background-gray-main)] border-b border-[var(--border-main)] rounded-t-[12px] shadow-[inset_0px_1px_0px_0px_#FFFFFF] dark:shadow-[inset_0px_1px_0px_0px_#FFFFFF30]"
  >
    <div class="flex-1 flex items-center justify-center">
      <div
        class="max-w-[250px] truncate text-[var(--text-tertiary)] text-sm font-medium text-center"
      >
        {{ fileName }}
      </div>
    </div>
  </div>
  <div class="flex-1 min-h-0 w-full overflow-y-auto">
    <div
      dir="ltr"
      data-orientation="horizontal"
      class="flex flex-col min-h-0 h-full relative"
    >
      <div
        data-state="active"
        data-orientation="horizontal"
        role="tabpanel"
        id="radix-:r2ke:-content-/home/ubuntu/llm_papers/todo.md"
        tabindex="0"
        class="focus-visible:outline-none data-[state=inactive]:hidden flex-1 min-h-0 h-full text-sm flex flex-col py-0 outline-none overflow-auto"
      >
        <section
          style="
            display: flex;
            position: relative;
            text-align: initial;
            width: 100%;
            height: 100%;
          "
        >
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
import { onMounted, ref, computed, watch, onUnmounted } from "vue";
import { ToolContent } from "@/types/message";
import { viewFile } from "@/api/agent";
import MonacoEditor from "@/components/ui/MonacoEditor.vue";
//import { showErrorToast } from "../utils/toast";
//import { useI18n } from "vue-i18n";

//const { t } = useI18n();

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
const refreshTimer = ref<number | null>(null);

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
  console.log("loadFileContent", props.live, filePath.value, props.toolContent.content);
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

// Start auto-refresh timer
const startAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
  }
  
  if (props.live && filePath.value) {
    refreshTimer.value = setInterval(() => {
      loadFileContent();
    }, 5000);
  }
};

// Stop auto-refresh timer
const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
    refreshTimer.value = null;
  }
};

// Watch for filename changes to reload content
watch(filePath, (newVal: string) => {
  if (newVal) {
    loadFileContent();
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
});

watch(() => props.toolContent, () => {
  loadFileContent();
});

watch(() => props.toolContent.timestamp, () => {
  loadFileContent();
});

// Watch for live prop changes
watch(() => props.live, (live: boolean) => {
  if (live) {
    loadFileContent();
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
});

// Load content when component is mounted
onMounted(() => {
  loadFileContent();
  startAutoRefresh();
});

onUnmounted(() => {
  stopAutoRefresh();
});
</script>
