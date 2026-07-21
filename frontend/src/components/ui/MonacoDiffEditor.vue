<template>
  <div ref="container" class="w-full h-full" />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue';
import * as monaco from 'monaco-editor/esm/vs/editor/editor.api';
import 'monaco-editor/esm/vs/language/json/monaco.contribution';
import 'monaco-editor/esm/vs/basic-languages/javascript/javascript.contribution';
import 'monaco-editor/esm/vs/basic-languages/typescript/typescript.contribution';
import 'monaco-editor/esm/vs/basic-languages/html/html.contribution';
import 'monaco-editor/esm/vs/basic-languages/css/css.contribution';
import 'monaco-editor/esm/vs/basic-languages/python/python.contribution';
import 'monaco-editor/esm/vs/basic-languages/java/java.contribution';
import 'monaco-editor/esm/vs/basic-languages/go/go.contribution';
import 'monaco-editor/esm/vs/basic-languages/markdown/markdown.contribution';

const props = withDefaults(defineProps<{
  original?: string;
  modified?: string;
  filename?: string;
  language?: string;
  theme?: string;
  fontSize?: number;
}>(), {
  original: '',
  modified: '',
  filename: '',
  language: '',
  theme: 'vs',
  fontSize: 14,
});

const container = ref<HTMLElement | null>(null);
let diffEditor: monaco.editor.IStandaloneDiffEditor | null = null;
let originalModel: monaco.editor.ITextModel | null = null;
let modifiedModel: monaco.editor.ITextModel | null = null;

const languageFromFilename = (filename: string): string => {
  const extension = filename.split('.').pop()?.toLowerCase() || '';
  const map: Record<string, string> = {
    js: 'javascript', ts: 'typescript', jsx: 'javascript', tsx: 'typescript',
    html: 'html', css: 'css', json: 'json', py: 'python', java: 'java',
    go: 'go', md: 'markdown', vue: 'html',
  };
  return map[extension] || 'plaintext';
};

const lang = computed(() => props.language || languageFromFilename(props.filename));

const init = () => {
  if (!container.value || diffEditor) return;
  originalModel = monaco.editor.createModel(props.original, lang.value);
  modifiedModel = monaco.editor.createModel(props.modified, lang.value);
  diffEditor = monaco.editor.createDiffEditor(container.value, {
    readOnly: true,
    renderSideBySide: false,
    renderOverviewRuler: false,
    automaticLayout: true,
    fontSize: props.fontSize,
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    theme: props.theme,
    originalEditable: false,
    lineNumbers: 'off',
    folding: false,
    glyphMargin: false,
    lineDecorationsWidth: 16,
    renderLineHighlight: 'none',
    padding: { top: 8, bottom: 8 },
  });
  diffEditor.setModel({ original: originalModel, modified: modifiedModel });
};

onMounted(init);

watch(() => props.original, (v) => originalModel?.setValue(v || ''));
watch(() => props.modified, (v) => modifiedModel?.setValue(v || ''));
watch(lang, (l) => {
  if (originalModel) monaco.editor.setModelLanguage(originalModel, l);
  if (modifiedModel) monaco.editor.setModelLanguage(modifiedModel, l);
});
watch(() => props.theme, (t) => {
  monaco.editor.setTheme(t);
});

onBeforeUnmount(() => {
  diffEditor?.dispose();
  diffEditor = null;
  originalModel?.dispose();
  modifiedModel?.dispose();
  originalModel = null;
  modifiedModel = null;
});
</script>

<style>
/* Match Manus inline diff: hide the original pane when not side-by-side */
.original-in-monaco-diff-editor {
  display: none;
}
</style>
