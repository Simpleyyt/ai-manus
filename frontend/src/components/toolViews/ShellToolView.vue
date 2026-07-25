<template>
  <div dir="ltr" class="flex flex-col flex-1 min-h-0 h-full w-full">
    <div
      ref="terminalEl"
      class="agent-workspace-terminal-panel flex-1 min-h-0 outline-none overflow-hidden w-full h-full"
      :class="isDark ? 'agent-workspace-terminal-panel-dark' : 'agent-workspace-terminal-panel-light'"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, toRef, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import { viewShellSession } from '@/api/agent';
import { ToolContent } from '@/types/message';
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

const terminalEl = ref<HTMLElement | null>(null);
const isDark = ref(false);

let term: Terminal | null = null;
let fitAddon: FitAddon | null = null;
let resizeObserver: ResizeObserver | null = null;
let themeObserver: MutationObserver | null = null;
let lastText = '';

const shellSessionId = computed(() => {
  if (props.toolContent && props.toolContent.args.id) {
    return props.toolContent.args.id;
  }
  return '';
});

const cssVar = (styles: CSSStyleDeclaration, name: string, fallback = '') =>
  styles.getPropertyValue(name).trim() || fallback;

/**
 * Official Manus tU(el, isDark): dark → bg/selection only;
 * light → full ANSI mapped from CSS vars.
 */
const xtermTheme = (dark: boolean) => {
  const styles = getComputedStyle(document.documentElement);
  const bg = cssVar(styles, '--background-gray-main', dark ? '#272728' : '#f8f8f7');
  const selection = cssVar(styles, '--background-selection', dark ? '#264f78' : '#b8d3f8');
  const thumb = cssVar(styles, '--terminal-panel-scrollbar-thumb', 'transparent');
  const thumbHover = cssVar(styles, '--terminal-panel-scrollbar-thumb-hover', thumb);
  const base = {
    background: bg,
    // Official: cursor matches canvas so it stays invisible with disableStdin
    cursor: bg,
    cursorAccent: bg,
    selectionBackground: selection,
    selectionInactiveBackground: selection,
    scrollbarSliderBackground: thumb,
    scrollbarSliderHoverBackground: thumbHover,
    scrollbarSliderActiveBackground: thumbHover,
  };
  if (dark) return base;

  const primary = cssVar(styles, '--text-primary', '#34322d');
  const secondary = cssVar(styles, '--text-secondary', '#858481');
  const tertiary = cssVar(styles, '--text-tertiary', '#b0aea5');
  const themePrimary = cssVar(styles, '--theme-text-primary', '#262626');
  const blue = cssVar(styles, '--text-blue', cssVar(styles, '--text-brand', '#0081f2'));
  const blueDark = cssVar(styles, '--text-blue-dark', blue);
  const error = cssVar(styles, '--function-error', '#f44336');
  const success = cssVar(styles, '--function-success', '#25ba3b');
  const warning = cssVar(styles, '--function-warning', '#ef9c2c');
  return {
    ...base,
    foreground: primary,
    black: primary,
    blue,
    brightBlack: tertiary,
    brightBlue: blue,
    brightCyan: blue,
    brightGreen: success,
    brightMagenta: blueDark,
    brightRed: error,
    brightWhite: themePrimary,
    brightYellow: warning,
    cyan: blue,
    green: success,
    magenta: blueDark,
    red: error,
    white: secondary,
    yellow: warning,
  };
};

const detectDark = () =>
  document.documentElement.classList.contains('dark')
  || document.body.classList.contains('dark');

/** Convert sandbox console entries to ANSI text for xterm. */
const consoleToText = (consoleData: unknown): string => {
  if (!consoleData) return '';
  if (typeof consoleData === 'string') return consoleData;
  if (!Array.isArray(consoleData)) return String(consoleData);
  const lines: string[] = [];
  for (const e of consoleData) {
    const ps1 = e?.ps1 ?? '';
    const command = e?.command ?? '';
    const output = e?.output ?? '';
    const head = ps1
      ? `\x1b[32m${ps1}\x1b[0m${command ? ` ${command}` : ''}`
      : command;
    lines.push(head);
    if (output) lines.push(String(output).replace(/\n/g, '\r\n'));
  }
  return lines.join('\r\n');
};

const writeTerminal = (text: string) => {
  if (!term || text === lastText) return;
  lastText = text;
  // Official: synchronized clear + home, then content
  term.write(`\x1b[?2026h\x1b[2J\x1b[3J\x1b[H${text}\x1b[?2026l`);
};

const fit = () => {
  try {
    fitAddon?.fit();
  } catch {
    // ignore fit errors during teardown
  }
};

const initTerminal = () => {
  if (!terminalEl.value || term) return;
  isDark.value = detectDark();
  // Official ManusComputer terminal options (mined): mono 14 / 1.15 — NOT system UI 16
  // overviewRuler needs a real canvas; omit in jsdom/unit tests
  const options: ConstructorParameters<typeof Terminal>[0] = {
    allowProposedApi: true,
    convertEol: true,
    cursorBlink: false,
    cursorInactiveStyle: 'none',
    cursorStyle: 'block',
    customGlyphs: true,
    disableStdin: true,
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
    fontSize: 14,
    lineHeight: 1.15,
    scrollback: 10000,
    theme: xtermTheme(isDark.value),
  };
  try {
    if (document.createElement('canvas').getContext('2d')) {
      options.overviewRuler = { width: 8 };
    }
  } catch {
    // jsdom: no canvas
  }
  term = new Terminal(options);
  fitAddon = new FitAddon();
  term.loadAddon(fitAddon);
  term.open(terminalEl.value);
  term.blur();
  fit();
  // Official skips first ResizeObserver fire (layout settle)
  let skipFirst = true;
  resizeObserver = new ResizeObserver(() => {
    if (skipFirst) {
      skipFirst = false;
      return;
    }
    fit();
  });
  resizeObserver.observe(terminalEl.value);
};

const loadShellContent = async () => {
  let consoleData: unknown;
  if (!props.live) {
    consoleData = props.toolContent.content?.console;
  } else {
    if (!shellSessionId.value) return;
    try {
      const response = await viewShellSession(props.sessionId, shellSessionId.value);
      consoleData = response.console;
    } catch (error) {
      console.error('Failed to load shell content:', error);
      return;
    }
  }
  await nextTick();
  if (!term) initTerminal();
  writeTerminal(consoleToText(consoleData));
  fit();
};

useLiveToolContent({
  toolContent: toRef(props, 'toolContent'),
  live: toRef(props, 'live'),
  targetKey: shellSessionId,
  load: loadShellContent,
});

watch(() => props.toolContent.content?.console, () => {
  if (!props.live) loadShellContent();
});

onMounted(() => {
  initTerminal();
  loadShellContent();
  themeObserver = new MutationObserver(() => {
    const dark = detectDark();
    if (dark !== isDark.value && term) {
      isDark.value = dark;
      term.options.theme = xtermTheme(dark);
    }
  });
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
});

onBeforeUnmount(() => {
  themeObserver?.disconnect();
  themeObserver = null;
  resizeObserver?.disconnect();
  resizeObserver = null;
  term?.dispose();
  term = null;
  fitAddon = null;
  lastText = '';
});
</script>
