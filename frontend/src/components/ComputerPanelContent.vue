<template>
  <!-- Manus agentWorkspace / computer detail shell -->
  <div
    id="manus-computer-detail"
    class="bg-[var(--background-gray-main)] sm:bg-[var(--background-menu-white)] sm:rounded-[16px] shadow-[0px_0px_8px_0px_rgba(0,0,0,0.02)] border border-black/8 dark:border-[var(--border-light)] flex h-full w-full overflow-hidden min-w-0">
    <div class="flex-1 min-w-0 flex flex-col h-full">
      <!-- Header — aligned with Manus FilePreviewerHeader: h-56 px-16 -->
      <div class="flex h-[56px] shrink-0 items-center justify-between gap-[16px] px-[16px] py-[12px] border-b border-[var(--border-main)]">
        <div class="text-[var(--text-primary)] text-lg font-semibold flex-1 truncate leading-[24px]">
          {{ $t("Manus's Computer") }}
        </div>

        <div class="flex items-center gap-1 shrink-0">
          <button
            type="button"
            class="size-[32px] rounded-[8px] inline-flex items-center justify-center hover:bg-[var(--fill-tsp-white-main)]"
            :title="viewMode === 'side' ? t('Center view') : t('Side view')"
            @click="toggleViewMode">
            <Columns2 v-if="viewMode === 'side'" :size="18" class="text-[var(--icon-tertiary)]" />
            <PanelRight v-else :size="18" class="text-[var(--icon-tertiary)]" />
          </button>

          <div class="relative" ref="appMenuRef">
            <button
              type="button"
              class="h-8 px-2 rounded-[8px] inline-flex items-center gap-1 cursor-pointer hover:bg-[var(--fill-tsp-white-main)] text-[var(--text-secondary)] text-xs"
              :title="t('Select an application to use')"
              @click="showAppMenu = !showAppMenu">
              <Monitor :size="16" />
              <ChevronDown :size="14" />
            </button>
            <div v-if="showAppMenu"
              class="absolute right-0 top-[calc(100%+6px)] z-50 min-w-[200px] rounded-[12px] border border-[var(--border-light)] bg-[var(--background-menu-white)] shadow-[0px_8px_32px_0px_var(--shadow-S)] py-1">
              <div class="px-3 py-1.5 text-[12px] text-[var(--text-tertiary)]">{{ t('Select an application to use') }}</div>
              <button
                v-for="app in apps"
                :key="app.key"
                type="button"
                class="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--fill-tsp-white-main)]"
                :class="preferredApp === app.key ? 'text-[var(--text-primary)] font-medium' : 'text-[var(--text-secondary)]'"
                @click="selectApp(app.key)">
                <component :is="app.icon" :size="16" />
                {{ app.label }}
                <Check v-if="preferredApp === app.key" :size="16" class="ml-auto" />
              </button>
            </div>
          </div>

          <button
            type="button"
            class="size-[32px] rounded-[8px] relative inline-flex items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-white-main)]"
            @click="hide">
            <X class="w-5 h-5 text-[var(--icon-tertiary)]" />
          </button>
        </div>
      </div>

      <div class="flex-1 min-h-0 flex flex-col px-[16px] pt-3 pb-4">
        <!-- Manus is using … -->
        <div v-if="toolInfo" class="flex items-center gap-2 mb-3">
          <div class="w-[40px] h-[40px] bg-[var(--fill-tsp-gray-main)] rounded-[10px] flex items-center justify-center flex-shrink-0">
            <component :is="toolInfo.icon" :size="28" />
          </div>
          <div class="flex-1 flex flex-col gap-1 min-w-0">
            <div class="text-[12px] leading-[16px] text-[var(--text-tertiary)]">
              {{ $t('Manus is using') }}
              <span class="text-[var(--text-secondary)]">{{ toolInfo.name }}</span>
            </div>
            <div
              class="max-w-[100%] w-[max-content] truncate text-[13px] rounded-full inline-flex items-center px-[10px] py-[3px] border border-[var(--border-light)] bg-[var(--fill-tsp-gray-main)] text-[var(--text-secondary)]">
              {{ toolInfo.function }}
              <span class="flex-1 min-w-0 px-1 ml-1 text-[12px] font-mono max-w-full text-ellipsis overflow-hidden whitespace-nowrap text-[var(--text-tertiary)]">
                <code>{{ toolInfo.functionArg }}</code>
              </span>
            </div>
          </div>
        </div>

        <div
          class="flex flex-col rounded-[12px] overflow-hidden bg-[var(--background-gray-main)] border border-[var(--border-main)] dark:border-black/30 shadow-[0px_4px_32px_0px_rgba(0,0,0,0.04)] flex-1 min-h-0">
          <component
            v-if="toolInfo"
            :is="toolInfo.view"
            :live="live"
            :sessionId="sessionId"
            :toolContent="toolContent"
            :isShare="isShare" />

          <!-- Timeline — Manus live / replay bar -->
          <div class="mt-auto flex w-full items-center gap-2 px-3 h-[48px] border-t border-[var(--border-main)] bg-[var(--background-menu-white)] shrink-0">
            <button type="button" class="size-8 rounded-full flex items-center justify-center hover:bg-[var(--fill-tsp-white-main)] disabled:opacity-40" :disabled="!canGoPrev" :title="t('Previous')" @click="goPrev">
              <SkipBack :size="16" class="text-[var(--icon-secondary)]" />
            </button>
            <button type="button" class="size-8 rounded-full flex items-center justify-center hover:bg-[var(--fill-tsp-white-main)]" :title="isPlaying ? t('Pause') : t('Play')" @click="togglePlay">
              <Pause v-if="isPlaying" :size="16" class="text-[var(--icon-secondary)]" />
              <PlayIcon v-else :size="16" class="text-[var(--icon-secondary)]" />
            </button>
            <button type="button" class="size-8 rounded-full flex items-center justify-center hover:bg-[var(--fill-tsp-white-main)] disabled:opacity-40" :disabled="!canGoNext" :title="t('Next')" @click="goNext">
              <SkipForward :size="16" class="text-[var(--icon-secondary)]" />
            </button>

            <div class="flex-1 mx-2 h-1.5 rounded-full bg-[var(--fill-tsp-white-dark)] relative overflow-hidden cursor-pointer" @click="seekByClick">
              <div
                class="absolute inset-y-0 left-0 bg-[var(--text-primary)] rounded-full"
                :class="{ 'transition-[width]': !isPlaying && !isScrubbing }"
                :style="{ width: `${progressPercent}%` }" />
            </div>

            <span class="font-mono text-[11px] tabular-nums text-[var(--text-tertiary)] shrink-0 min-w-[4.5rem] text-right">
              {{ clockLabel }}
            </span>

            <button
              v-if="!realTime"
              type="button"
              class="h-8 px-3 border border-[var(--border-main)] flex items-center gap-1 bg-[var(--background-white-main)] hover:bg-[var(--background-gray-main)] rounded-full cursor-pointer"
              @click="jumpToRealTime">
              <span class="text-[var(--text-primary)] text-xs font-medium">{{ $t('Jump to live') }}</span>
            </button>

            <div class="flex items-center gap-1.5 text-[12px] text-[var(--text-tertiary)] shrink-0">
              <span class="inline-block size-2 rounded-full" :class="live || realTime ? 'bg-[var(--function-success)]' : 'bg-[var(--icon-tertiary)]'" />
              {{ live || realTime ? t('live') : t('Replay') }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toRef, ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import {
  PlayIcon, Monitor, ChevronDown, Globe, Terminal, Check, X,
  SkipBack, SkipForward, Pause, Columns2, PanelRight, FileText, Search,
} from 'lucide-vue-next';
import type { ToolContent } from '@/types/message';
import { useToolInfo } from '@/composables/useTool';

export type ComputerApp = 'browser' | 'terminal' | 'file' | 'search';

const props = withDefaults(defineProps<{
  sessionId?: string;
  realTime: boolean;
  toolContent: ToolContent;
  live: boolean;
  isShare: boolean;
  toolHistory?: ToolContent[];
}>(), {
  toolHistory: () => [],
});

const { t } = useI18n();
const { toolInfo } = useToolInfo(toRef(props, 'toolContent'));

const showAppMenu = ref(false);
const appMenuRef = ref<HTMLElement | null>(null);
const preferredApp = ref<ComputerApp>('browser');
const viewMode = ref<'side' | 'center'>('side');
const isPlaying = ref(false);
const isScrubbing = ref(false);
/** Absolute playhead in Unix seconds (manual / replay). Ignored while realTime. */
const playheadTs = ref(0);
/** Wall-clock tick so live end / playhead can advance in real time. */
const nowSec = ref(Math.floor(Date.now() / 1000));
let playRaf: number | null = null;
let clockTimer: ReturnType<typeof setInterval> | null = null;
let playWallStartMs = 0;
let playheadStartTs = 0;

const apps = computed(() => [
  { key: 'browser' as const, label: t('Browser'), icon: Globe },
  { key: 'terminal' as const, label: t('Terminal'), icon: Terminal },
  { key: 'file' as const, label: t('File'), icon: FileText },
  { key: 'search' as const, label: t('Information'), icon: Search },
]);

/** Normalize event timestamps to Unix seconds (backend sends seconds; tolerate ms). */
const toUnixSec = (ts?: number): number => {
  if (ts == null || !Number.isFinite(ts)) return nowSec.value;
  if (ts > 1e12) return Math.floor(ts / 1000);
  return Math.floor(ts);
};

const history = computed(() => {
  const raw = props.toolHistory?.length
    ? props.toolHistory
    : (props.toolContent ? [props.toolContent] : []);
  return [...raw].sort((a, b) => {
    const dt = toUnixSec(a.timestamp) - toUnixSec(b.timestamp);
    if (dt !== 0) return dt;
    return String(a.tool_call_id).localeCompare(String(b.tool_call_id));
  });
});

const timelineStart = computed(() => {
  if (!history.value.length) return nowSec.value;
  return toUnixSec(history.value[0].timestamp);
});

const timelineEnd = computed(() => {
  if (!history.value.length) return nowSec.value;
  const last = toUnixSec(history.value[history.value.length - 1].timestamp);
  // While live at the edge, grow the end with wall clock so the bar is real time.
  if (props.realTime && props.live) {
    return Math.max(last, nowSec.value);
  }
  return Math.max(last, timelineStart.value);
});

const timelineDuration = computed(() => Math.max(1, timelineEnd.value - timelineStart.value));

const effectivePlayhead = computed(() => {
  if (props.realTime) return timelineEnd.value;
  return Math.min(timelineEnd.value, Math.max(timelineStart.value, playheadTs.value));
});

const progressPercent = computed(() => {
  if (timelineDuration.value <= 0) return 100;
  return ((effectivePlayhead.value - timelineStart.value) / timelineDuration.value) * 100;
});

const formatClock = (seconds: number): string => {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  }
  return `${m}:${String(sec).padStart(2, '0')}`;
};

const clockLabel = computed(() => {
  const elapsed = effectivePlayhead.value - timelineStart.value;
  return `${formatClock(elapsed)} / ${formatClock(timelineDuration.value)}`;
});

const currentIndex = computed(() => {
  const id = props.toolContent?.tool_call_id;
  if (!id) return Math.max(0, history.value.length - 1);
  const idx = history.value.findIndex((tool) => tool.tool_call_id === id);
  return idx >= 0 ? idx : Math.max(0, history.value.length - 1);
});

const canGoPrev = computed(() => currentIndex.value > 0);
const canGoNext = computed(() => currentIndex.value < history.value.length - 1);

const emit = defineEmits<{
  (e: 'jumpToRealTime'): void;
  (e: 'hide'): void;
  (e: 'selectTool', tool: ToolContent): void;
  (e: 'selectApp', app: ComputerApp): void;
}>();

const hide = () => emit('hide');
const jumpToRealTime = () => {
  stopPlay();
  playheadTs.value = timelineEnd.value;
  emit('jumpToRealTime');
};

const selectApp = (app: ComputerApp) => {
  preferredApp.value = app;
  showAppMenu.value = false;
  emit('selectApp', app);
};

const toggleViewMode = () => {
  viewMode.value = viewMode.value === 'side' ? 'center' : 'side';
};

/** Last tool whose timestamp is <= t (timeline scrub mapping). */
const toolAtTime = (t: number): ToolContent | undefined => {
  if (!history.value.length) return undefined;
  let selected = history.value[0];
  for (const tool of history.value) {
    if (toUnixSec(tool.timestamp) <= t) selected = tool;
    else break;
  }
  return selected;
};

const selectAtPlayhead = (t: number) => {
  playheadTs.value = t;
  const tool = toolAtTime(t);
  if (tool && tool.tool_call_id !== props.toolContent?.tool_call_id) {
    emit('selectTool', tool);
  }
};

const goPrev = () => {
  if (!canGoPrev.value) return;
  stopPlay();
  const tool = history.value[currentIndex.value - 1];
  playheadTs.value = toUnixSec(tool.timestamp);
  emit('selectTool', tool);
};

const goNext = () => {
  if (!canGoNext.value) return;
  stopPlay();
  const tool = history.value[currentIndex.value + 1];
  playheadTs.value = toUnixSec(tool.timestamp);
  emit('selectTool', tool);
};

const stopPlay = () => {
  isPlaying.value = false;
  if (playRaf != null) {
    cancelAnimationFrame(playRaf);
    playRaf = null;
  }
};

const tickPlay = () => {
  const elapsedSec = (Date.now() - playWallStartMs) / 1000;
  const next = playheadStartTs + elapsedSec;
  if (next >= timelineEnd.value) {
    playheadTs.value = timelineEnd.value;
    const tool = toolAtTime(timelineEnd.value);
    if (tool) emit('selectTool', tool);
    stopPlay();
    if (props.live) emit('jumpToRealTime');
    return;
  }
  selectAtPlayhead(next);
  playRaf = requestAnimationFrame(tickPlay);
};

const togglePlay = () => {
  if (isPlaying.value) {
    stopPlay();
    return;
  }
  // Already at the live edge — nothing to play forward.
  if (props.realTime && props.live) return;
  if (effectivePlayhead.value >= timelineEnd.value - 0.05) {
    // Restart from the beginning of the timeline.
    playheadTs.value = timelineStart.value;
    const first = history.value[0];
    if (first) emit('selectTool', first);
  }
  isPlaying.value = true;
  playWallStartMs = Date.now();
  playheadStartTs = playheadTs.value || timelineStart.value;
  playRaf = requestAnimationFrame(tickPlay);
};

const seekByClick = (event: MouseEvent) => {
  const el = event.currentTarget as HTMLElement;
  const rect = el.getBoundingClientRect();
  const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
  const t = timelineStart.value + ratio * timelineDuration.value;
  stopPlay();
  isScrubbing.value = true;
  selectAtPlayhead(t);
  requestAnimationFrame(() => {
    isScrubbing.value = false;
  });
};

const inferApp = (tool?: ToolContent): ComputerApp => {
  const name = (tool?.name || '').toLowerCase();
  if (name.includes('shell')) return 'terminal';
  if (name.includes('file')) return 'file';
  if (name.includes('info') || name.includes('search')) return 'search';
  return 'browser';
};

watch(() => props.toolContent, (tool) => {
  preferredApp.value = inferApp(tool);
  if (!isPlaying.value && !props.realTime && tool) {
    playheadTs.value = toUnixSec(tool.timestamp);
  }
});

watch(
  () => props.realTime,
  (rt) => {
    if (rt) {
      stopPlay();
      playheadTs.value = timelineEnd.value;
    } else if (props.toolContent) {
      playheadTs.value = toUnixSec(props.toolContent.timestamp);
    }
  },
);

const handleClickOutside = (event: MouseEvent) => {
  if (showAppMenu.value && appMenuRef.value && !appMenuRef.value.contains(event.target as Node)) {
    showAppMenu.value = false;
  }
};

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside);
  preferredApp.value = inferApp(props.toolContent);
  playheadTs.value = props.toolContent
    ? toUnixSec(props.toolContent.timestamp)
    : timelineEnd.value;
  clockTimer = setInterval(() => {
    nowSec.value = Math.floor(Date.now() / 1000);
  }, 250);
});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside);
  stopPlay();
  if (clockTimer) {
    clearInterval(clockTimer);
    clockTimer = null;
  }
});
</script>
