<template>
  <div class="bg-[var(--background-gray-main)] sm:bg-[var(--background-menu-white)] sm:rounded-[22px] shadow-[0px_0px_8px_0px_rgba(0,0,0,0.02)] border border-black/8 dark:border-[var(--border-light)] flex h-full w-full">
    <div class="flex-1 min-w-0 p-4 flex flex-col h-full">
      <!-- Manus's Computer header -->
      <div class="flex items-center gap-2 w-full">
        <div class="text-[var(--text-primary)] text-lg font-semibold flex-1 truncate">{{ $t("Manus's Computer") }}</div>

        <button
          type="button"
          class="w-7 h-7 rounded-md inline-flex items-center justify-center hover:bg-[var(--fill-tsp-gray-main)]"
          :title="viewMode === 'side' ? t('Center view') : t('Side view')"
          @click="toggleViewMode">
          <Columns2 v-if="viewMode === 'side'" :size="16" class="text-[var(--icon-tertiary)]" />
          <PanelRight v-else :size="16" class="text-[var(--icon-tertiary)]" />
        </button>

        <div class="relative" ref="appMenuRef">
          <button
            type="button"
            class="h-7 px-2 rounded-md inline-flex items-center gap-1 cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] text-[var(--text-secondary)] text-xs"
            :title="t('Select an application to use')"
            @click="showAppMenu = !showAppMenu">
            <Monitor :size="14" />
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
          class="w-7 h-7 relative rounded-md inline-flex items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)]"
          @click="hide">
          <X class="w-5 h-5 text-[var(--icon-tertiary)]" />
        </button>
      </div>

      <div v-if="toolInfo" class="flex items-center gap-2 mt-2">
        <div class="w-[40px] h-[40px] bg-[var(--fill-tsp-gray-main)] rounded-lg flex items-center justify-center flex-shrink-0">
          <component :is="toolInfo.icon" :size="28" />
        </div>
        <div class="flex-1 flex flex-col gap-1 min-w-0">
          <div class="text-[12px] text-[var(--text-tertiary)]">
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
        class="flex flex-col rounded-[12px] overflow-hidden bg-[var(--background-gray-main)] border border-[var(--border-dark)] dark:border-black/30 shadow-[0px_4px_32px_0px_rgba(0,0,0,0.04)] flex-1 min-h-0 mt-[16px]">
        <component
          v-if="toolInfo"
          :is="toolInfo.view"
          :live="live"
          :sessionId="sessionId"
          :toolContent="toolContent"
          :isShare="isShare" />

        <!-- Live / replay timeline (Manus computer bottom bar) -->
        <div class="mt-auto flex w-full items-center gap-2 px-3 h-[48px] border-t border-[var(--border-light)] bg-[var(--background-menu-white)]">
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
            <div class="absolute inset-y-0 left-0 bg-[var(--text-primary)] rounded-full transition-[width]" :style="{ width: `${progressPercent}%` }" />
          </div>

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
let playTimer: ReturnType<typeof setInterval> | null = null;

const apps = computed(() => [
  { key: 'browser' as const, label: t('Browser'), icon: Globe },
  { key: 'terminal' as const, label: t('Terminal'), icon: Terminal },
  { key: 'file' as const, label: t('File'), icon: FileText },
  { key: 'search' as const, label: t('Information'), icon: Search },
]);

const history = computed(() => props.toolHistory?.length ? props.toolHistory : (props.toolContent ? [props.toolContent] : []));

const currentIndex = computed(() => {
  const id = props.toolContent?.tool_call_id;
  if (!id) return Math.max(0, history.value.length - 1);
  const idx = history.value.findIndex((t) => t.tool_call_id === id);
  return idx >= 0 ? idx : Math.max(0, history.value.length - 1);
});

const progressPercent = computed(() => {
  if (history.value.length <= 1) return (props.live || props.realTime) ? 100 : 100;
  return ((currentIndex.value + 1) / history.value.length) * 100;
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

const goPrev = () => {
  if (!canGoPrev.value) return;
  stopPlay();
  emit('selectTool', history.value[currentIndex.value - 1]);
};

const goNext = () => {
  if (!canGoNext.value) return;
  emit('selectTool', history.value[currentIndex.value + 1]);
};

const stopPlay = () => {
  isPlaying.value = false;
  if (playTimer) {
    clearInterval(playTimer);
    playTimer = null;
  }
};

const togglePlay = () => {
  if (isPlaying.value) {
    stopPlay();
    return;
  }
  if (props.realTime && props.live) {
    // already live — no-op replay
    return;
  }
  isPlaying.value = true;
  playTimer = setInterval(() => {
    if (currentIndex.value >= history.value.length - 1) {
      stopPlay();
      emit('jumpToRealTime');
      return;
    }
    emit('selectTool', history.value[currentIndex.value + 1]);
  }, 1200);
};

const seekByClick = (event: MouseEvent) => {
  const el = event.currentTarget as HTMLElement;
  const rect = el.getBoundingClientRect();
  const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
  const idx = Math.min(history.value.length - 1, Math.floor(ratio * history.value.length));
  if (history.value[idx]) {
    stopPlay();
    emit('selectTool', history.value[idx]);
  }
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
});

const handleClickOutside = (event: MouseEvent) => {
  if (showAppMenu.value && appMenuRef.value && !appMenuRef.value.contains(event.target as Node)) {
    showAppMenu.value = false;
  }
};

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside);
  preferredApp.value = inferApp(props.toolContent);
});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside);
  stopPlay();
});
</script>
