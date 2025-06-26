<template>
  <div ref="monacoContainer" style="width: 100%; height: 100%"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed } from "vue";
import * as monaco from "monaco-editor/esm/vs/editor/editor.api";

// Import language contributions
import "monaco-editor/esm/vs/language/json/monaco.contribution";
import "monaco-editor/esm/vs/basic-languages/javascript/javascript.contribution";
import "monaco-editor/esm/vs/basic-languages/typescript/typescript.contribution";
import "monaco-editor/esm/vs/basic-languages/html/html.contribution";
import "monaco-editor/esm/vs/basic-languages/css/css.contribution";
import "monaco-editor/esm/vs/basic-languages/python/python.contribution";
import "monaco-editor/esm/vs/basic-languages/java/java.contribution";
import "monaco-editor/esm/vs/basic-languages/go/go.contribution";
import "monaco-editor/esm/vs/basic-languages/markdown/markdown.contribution";

interface MonacoEditorProps {
  value?: string;
  language?: string;
  filename?: string;
  readOnly?: boolean;
  theme?: string;
  lineNumbers?: 'on' | 'off' | 'relative' | 'interval';
  wordWrap?: 'on' | 'off' | 'wordWrapColumn' | 'bounded';
  minimap?: boolean;
  scrollBeyondLastLine?: boolean;
  automaticLayout?: boolean;
}

const props = withDefaults(defineProps<MonacoEditorProps>(), {
  value: "",
  language: "",
  filename: "",
  readOnly: true,
  theme: "vs",
  lineNumbers: "off",
  wordWrap: "on",
  minimap: false,
  scrollBeyondLastLine: false,
  automaticLayout: true,
});

const emit = defineEmits<{
  ready: [editor: monaco.editor.IStandaloneCodeEditor];
  change: [value: string];
}>();

const monacoContainer = ref<HTMLElement | null>(null);
let editor: monaco.editor.IStandaloneCodeEditor | null = null;

// Language mapping based on filename or explicit language
const languageFromFilename = (filename: string): string => {
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

const computedLanguage = computed(() => {
  if (props.language) {
    return props.language;
  }
  if (props.filename) {
    return languageFromFilename(props.filename);
  }
  return "plaintext";
});

// Initialize Monaco editor
const initEditor = () => {
  if (!monacoContainer.value || editor) {
    return;
  }

  editor = monaco.editor.create(monacoContainer.value, {
    value: props.value,
    language: computedLanguage.value,
    theme: props.theme,
    readOnly: props.readOnly,
    minimap: { enabled: props.minimap },
    scrollBeyondLastLine: props.scrollBeyondLastLine,
    automaticLayout: props.automaticLayout,
    lineNumbers: props.lineNumbers,
    wordWrap: props.wordWrap,
    scrollbar: {
      vertical: "auto",
      horizontal: "auto",
    },
  });

  // Emit ready event
  emit("ready", editor);

  // Listen for content changes
  if (!props.readOnly) {
    editor.onDidChangeModelContent(() => {
      if (editor) {
        emit("change", editor.getValue());
      }
    });
  }
};

// Update editor content
const updateContent = (newValue: string) => {
  if (editor) {
    const model = editor.getModel();
    if (model) {
      model.setValue(newValue);
    } else {
      editor.setValue(newValue);
    }
  }
};

// Update editor language
const updateLanguage = (newLanguage: string) => {
  if (editor) {
    const model = editor.getModel();
    if (model) {
      monaco.editor.setModelLanguage(model, newLanguage);
    }
  }
};

// Expose methods to parent component
defineExpose({
  editor: () => editor,
  updateContent,
  updateLanguage,
  getValue: () => editor?.getValue() || "",
});

// Watch for value changes
watch(() => props.value, (newValue) => {
  if (newValue !== editor?.getValue()) {
    updateContent(newValue);
  }
});

// Watch for language changes
watch(computedLanguage, (newLanguage) => {
  updateLanguage(newLanguage);
});

onMounted(() => {
  initEditor();
});

onBeforeUnmount(() => {
  if (editor) {
    editor.dispose();
    editor = null;
  }
});
</script> 