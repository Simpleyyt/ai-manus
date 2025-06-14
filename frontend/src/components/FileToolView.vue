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
          <div ref="monacoContainer" style="width: 100%; height: 100%"></div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch, onBeforeUnmount, onUnmounted } from "vue";
import { ToolContent } from "../types/message";
import { viewFile } from "../api/agent";
import * as monaco from "monaco-editor/esm/vs/editor/editor.api";
//import { showErrorToast } from "../utils/toast";
//import { useI18n } from "vue-i18n";

import "monaco-editor/esm/vs/language/json/monaco.contribution";
import "monaco-editor/esm/vs/basic-languages/javascript/javascript.contribution";
import "monaco-editor/esm/vs/basic-languages/typescript/typescript.contribution";
import "monaco-editor/esm/vs/basic-languages/html/html.contribution";
import "monaco-editor/esm/vs/basic-languages/css/css.contribution";
import "monaco-editor/esm/vs/basic-languages/python/python.contribution";
import "monaco-editor/esm/vs/basic-languages/java/java.contribution";
import "monaco-editor/esm/vs/basic-languages/go/go.contribution";
import "monaco-editor/esm/vs/basic-languages/markdown/markdown.contribution";

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
const monacoContainer = ref<HTMLElement | null>(null);
const cancelViewFile = ref<(() => void) | null>(null);

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

let editor: monaco.editor.IStandaloneCodeEditor | null = null;

// Infer language based on filename
const getLanguage = (filename: string): string => {
  const extension = filename.split(".").pop()?.toLowerCase() || "";
  const languageMap: Record<string, string> = {
    js: "javascript",
    ts: "typescript",
    html: "html",
    css: "css",
    json: "json",
    py: "python",
    java: "java",
    c: "c",
    cpp: "cpp",
    go: "go",
    md: "markdown",
    txt: "plaintext",
    vue: "html",
    jsx: "javascript",
    tsx: "typescript",
  };

  return languageMap[extension] || "plaintext";
};

// Initialize Monaco editor
const initMonacoEditor = () => {
  if (monacoContainer.value) {
    // If editor already exists, return
    if (editor) {
      return;
    }

    const language = getLanguage(filePath.value);

    editor = monaco.editor.create(monacoContainer.value, {
      value: "",
      language,
      theme: "vs",
      readOnly: true,
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      automaticLayout: true,
      lineNumbers: "off",
      wordWrap: "on",
      scrollbar: {
        vertical: "auto",
        horizontal: "auto",
      },
    });
  }
};

// Load file content
const loadFileContent = async () => {
  if (!props.live) {
    fileContent.value = props.toolContent.content?.content || "";
    return;
  }
  if (!filePath.value) return;
  if (cancelViewFile.value) {
    cancelViewFile.value();
    cancelViewFile.value = null;
  }
  cancelViewFile.value = await viewFile(props.sessionId, filePath.value, {
    onMessage: (event) => {
      if (event.event === "file") {
        fileContent.value = event.data.content;
      }
    }
  })
};

watch(fileContent, () => {
  if (editor) {
    // Use editor model to directly update content, reducing re-rendering overhead
    const model = editor.getModel();
    if (model) {
      model.setValue(fileContent.value);
    } else {
      editor.setValue(fileContent.value);
    }
    monaco.editor.setModelLanguage(editor.getModel()!, getLanguage(filePath.value));
  }
});

// Watch for filename changes to reload content
watch(filePath, (newVal) => {
  if (newVal) {
    loadFileContent();
  }
});

watch(() => props.toolContent.status, () => {
  loadFileContent();
});

// Load content and set up refresh timer when component is mounted
onMounted(() => {
  initMonacoEditor();
  loadFileContent();
});

// Clean up editor and timer before component unmounts
onBeforeUnmount(() => {
  if (editor) {
    editor.dispose();
    editor = null;
  }
});

onUnmounted(() => {
  if (cancelViewFile.value) {
    cancelViewFile.value();
    cancelViewFile.value = null;
  }
});
</script>
