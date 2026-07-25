<template>
  <div
    ref="monacoContainer"
    class="h-full w-full"
    :class="panelClass"
  />
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
import "monaco-editor/esm/vs/basic-languages/shell/shell.contribution";

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
  /** Official CodePreviewer: padding.top 15; Computer default 8 */
  paddingTop?: number;
  /** Official CodePreviewer: 0; Computer default 16 */
  lineDecorationsWidth?: number;
  /** Official CodePreviewer: true; Computer default false */
  folding?: boolean;
  /** Official CodePreviewer scrollbar size 6; omit for Monaco default auto */
  scrollbarSize?: number;
  fontSize?: number;
  lineHeight?: number;
  fontFamily?: string;
  panelClass?: string;
  lineNumbersMinChars?: number;
  /**
   * Paste official CodePreviewer MONACO_COMMON_OPTIONS + one-light (#fafafa).
   * Ignores Computer-oriented defaults that fight gutter/line-number chrome.
   */
  variant?: 'default' | 'codePreviewer';
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
  paddingTop: 8,
  lineDecorationsWidth: 16,
  folding: false,
  fontSize: 14,
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
  panelClass: "",
  variant: "default",
});

let filePreviewerThemeDefined = false;

/** Official one-light colors (4445yl2k5als_.js) + CodePreviewer bg override #fafafa */
const ensureFilePreviewerTheme = () => {
  if (filePreviewerThemeDefined) return;
  monaco.editor.defineTheme("one-light-file-preview", {
    base: "vs",
    inherit: true,
    rules: [],
    colors: {
      "editor.background": "#fafafa",
      "editor.foreground": "#24292e",
      "editor.lineHighlightBackground": "#f6f8fa",
      "editor.selectionBackground": "#0366d625",
      "editor.inactiveSelectionBackground": "#0366d611",
      "editorGutter.background": "#fafafa",
      "editorLineNumber.foreground": "#1b1f234d",
      "editorLineNumber.activeForeground": "#24292e",
      "editorCursor.foreground": "#044289",
      "editorIndentGuide.background": "#eff2f6",
      "editorIndentGuide.activeBackground": "#d7dbe0",
      "editorWhitespace.foreground": "#d1d5da",
      "editorBracketHighlight.foreground1": "#005cc5",
      "editorBracketHighlight.foreground2": "#e36209",
      "editorBracketHighlight.foreground3": "#5a32a3",
    },
  });
  filePreviewerThemeDefined = true;
};

const emit = defineEmits<{
  ready: [editor: monaco.editor.IStandaloneCodeEditor];
  change: [value: string];
}>();

const monacoContainer = ref<HTMLElement | null>(null);
let editor: monaco.editor.IStandaloneCodeEditor | null = null;

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
    sh: "shell",
    bash: "shell",
  };
  return languageMap[extension] || "plaintext";
};

const computedLanguage = computed(() => {
  if (props.language) {
    // Official: bash → shell
    return props.language === "bash" ? "shell" : props.language;
  }
  if (props.filename) {
    return languageFromFilename(props.filename);
  }
  return "plaintext";
});

/** Official MONACO_COMMON_OPTIONS + lineNumbers on (FilePreviewerContent) */
const buildCodePreviewerOptions = (): monaco.editor.IStandaloneEditorConstructionOptions => {
  const lang = computedLanguage.value;
  const options: monaco.editor.IStandaloneEditorConstructionOptions = {
    value: props.value,
    language: lang,
    theme: "one-light-file-preview",
    readOnly: true,
    folding: true,
    lineDecorationsWidth: 0,
    renderValidationDecorations: "off",
    scrollBeyondLastLine: false,
    lineNumbers: "on",
    wordWrap: "on",
    stickyScroll: { enabled: false },
    unicodeHighlight: {
      ambiguousCharacters: false,
      invisibleCharacters: false,
      nonBasicASCII: false,
    },
    scrollbar: {
      verticalScrollbarSize: 6,
      horizontalScrollbarSize: 6,
    },
    minimap: { enabled: false },
    padding: { top: 15 },
    automaticLayout: true,
    // Do NOT set lineNumbersMinChars / glyphMargin / renderLineHighlight —
    // official omits them (Monaco defaults).
  };

  // Official getLanguageSpecificOptions for plaintext
  if (lang === "plaintext") {
    options.fontSize = 16;
    options.lineHeight = 24;
    options.fontFamily = "Arial, Helvetica, sans-serif";
  }

  return options;
};

const buildDefaultOptions = (): monaco.editor.IStandaloneEditorConstructionOptions => {
  const scrollbar = props.scrollbarSize != null
    ? {
        verticalScrollbarSize: props.scrollbarSize,
        horizontalScrollbarSize: props.scrollbarSize,
      }
    : {
        vertical: "auto" as const,
        horizontal: "auto" as const,
      };

  const lineNumbersMinChars = props.lineNumbersMinChars ?? (props.lineNumbers === "off" ? 0 : 5);

  return {
    value: props.value,
    language: computedLanguage.value,
    theme: props.theme,
    readOnly: props.readOnly,
    fontSize: props.fontSize,
    lineHeight: props.lineHeight,
    fontFamily: props.fontFamily,
    minimap: { enabled: props.minimap },
    scrollBeyondLastLine: props.scrollBeyondLastLine,
    automaticLayout: props.automaticLayout,
    lineNumbers: props.lineNumbers,
    wordWrap: props.wordWrap,
    folding: props.folding,
    glyphMargin: false,
    lineDecorationsWidth: props.lineDecorationsWidth,
    lineNumbersMinChars,
    renderLineHighlight: "none",
    renderValidationDecorations: "off",
    stickyScroll: { enabled: false },
    overviewRulerLanes: 0,
    hideCursorInOverviewRuler: true,
    overviewRulerBorder: false,
    padding: { top: props.paddingTop, bottom: 8 },
    scrollbar,
  };
};

const initEditor = () => {
  if (!monacoContainer.value || editor) {
    return;
  }

  if (props.variant === "codePreviewer") {
    ensureFilePreviewerTheme();
    editor = monaco.editor.create(monacoContainer.value, buildCodePreviewerOptions());
  } else {
    editor = monaco.editor.create(monacoContainer.value, buildDefaultOptions());
  }

  emit("ready", editor);

  if (!props.readOnly) {
    editor.onDidChangeModelContent(() => {
      if (editor) {
        emit("change", editor.getValue());
      }
    });
  }
};

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

const updateLanguage = (newLanguage: string) => {
  if (editor) {
    const model = editor.getModel();
    if (model) {
      monaco.editor.setModelLanguage(model, newLanguage);
    }
  }
};

defineExpose({
  editor: () => editor,
  updateContent,
  updateLanguage,
  getValue: () => editor?.getValue() || "",
});

watch(() => props.value, (newValue) => {
  if (newValue !== editor?.getValue()) {
    updateContent(newValue);
  }
});

watch(computedLanguage, (newLanguage) => {
  updateLanguage(newLanguage);
  if (props.variant === "codePreviewer" && editor) {
    if (newLanguage === "plaintext") {
      editor.updateOptions({
        fontSize: 16,
        lineHeight: 24,
        fontFamily: "Arial, Helvetica, sans-serif",
      });
    } else {
      editor.updateOptions({
        fontSize: undefined,
        lineHeight: undefined,
        fontFamily: undefined,
      });
    }
  }
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
