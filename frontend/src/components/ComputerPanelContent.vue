<template>
  <!-- Official ManusComputer: Header | Panel | Timeline | Planner -->
  <div
    id="manus-agent-workspace"
    class="h-full flex flex-col bg-[var(--background-gray-main)]"
    :class="shellClass">
    <!-- ManusComputerHeader (mined eg) -->
    <div class="flex h-[56px] items-center gap-[8px] border-b border-[var(--border-main)] px-[16px] py-[12px]">
      <div class="flex min-w-0 flex-1 flex-col justify-center">
        <h2 class="truncate text-[14px] font-[500] text-[var(--text-primary)]">
          {{ $t("{name}'s computer", { name: 'Manus' }) }}
        </h2>
        <div class="flex min-w-0 items-center gap-[8px] text-[var(--text-tertiary)] text-xs">
          <div class="" :title="usingLabel">
            <template v-if="toolInfo">
              {{ $t('Manus is using') }}<span>{{ toolInfo.name }}</span>
            </template>
            <template v-else>
              {{ $t('Waiting for instructions') }}
            </template>
          </div>
          <div class="h-[12px] w-px shrink-0 bg-[var(--border-main)]" />
          <div
            class="min-w-0 flex-1 truncate"
            :class="{ 'animate-shimmer bg-[linear-gradient(110deg,var(--text-tertiary),35%,var(--text-shining),50%,var(--text-tertiary),75%,var(--text-tertiary))] bg-[length:200%_100%] bg-clip-text text-transparent': isStreamingAction }"
            :title="actionLabel">
            <template v-if="toolInfo">
              {{ toolInfo.function }}<span
                v-if="toolInfo.functionArg"
                class="ms-[4px] font-mono">{{ toolInfo.functionArg }}</span>
            </template>
            <template v-else>
              {{ $t('Waiting for instructions') }}
            </template>
          </div>
        </div>
      </div>

      <div class="flex shrink-0 items-center gap-[4px]">
        <!-- Use {product}'s computer — official button tokens -->
        <div v-if="!isShare" class="relative" ref="useComputerRef">
          <button
            type="button"
            class="flex items-center justify-end gap-[1px] clickable px-[6px] py-1 hover:bg-[var(--fill-tsp-white-light)] rounded-md !size-[32px] justify-center !rounded-[8px] !p-0 text-[var(--icon-secondary)] [&_svg]:!size-[18px]"
            :class="{ 'bg-[var(--fill-tsp-gray-main)]': showUseComputer }"
            :aria-expanded="showUseComputer"
            aria-haspopup="dialog"
            :title="useComputerTitle"
            @click="showUseComputer = !showUseComputer">
            <Monitor :size="18" />
          </button>
          <div
            v-if="showUseComputer"
            class="absolute right-0 top-[calc(100%+10px)] z-50 w-[min(480px,calc(100vw-32px))] rounded-[20px] border border-[var(--border-main)] bg-[var(--background-menu-white)] shadow-[0px_8px_32px_0px_var(--shadow-S)] p-4 flex flex-col gap-3">
            <div class="flex justify-between items-center">
              <div class="flex items-center gap-1.5 min-w-0">
                <Monitor :size="20" class="text-[var(--icon-primary)] shrink-0" />
                <h2 class="text-lg text-[var(--text-primary)] font-serif font-semibold truncate">
                  {{ t("Use application on {product}'s computer", { product: 'Manus' }) }}
                </h2>
              </div>
              <button
                type="button"
                class="size-8 rounded-[8px] inline-flex items-center justify-center hover:bg-[var(--fill-tsp-white-main)]"
                :title="t('Close')"
                @click="showUseComputer = false">
                <X :size="16" class="text-[var(--icon-tertiary)]" />
              </button>
            </div>
            <div class="text-[var(--text-secondary)] text-[13px] leading-[18px]">
              <span>{{ t("You're about to use {product}'s computer. ", { product: 'Manus' }) }}</span>
              <span class="text-[var(--text-primary)]">{{ t('When finished, please inform {product} of your changes to help it work effectively.', { product: 'Manus' }) }}</span>
            </div>
            <div class="flex justify-end gap-2 mt-[4px]">
              <button
                type="button"
                class="h-9 px-4 rounded-[10px] text-sm text-[var(--text-secondary)] hover:bg-[var(--fill-tsp-white-main)]"
                @click="showUseComputer = false">
                {{ t('Cancel') }}
              </button>
              <button
                type="button"
                class="h-9 px-4 rounded-[10px] text-sm bg-[var(--Button-primary-black)] text-[var(--text-onblack)] hover:opacity-90"
                @click="confirmUseComputer">
                {{ t('Use application') }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="!isShare" class="flex items-center px-[4px]">
          <div class="h-[16px] w-px bg-[var(--border-dark)]" />
        </div>

        <!-- Official IconButton Side/Center (!isMobile) -->
        <div
          v-if="!isMobile"
          role="button"
          tabindex="0"
          class="flex h-7 w-7 items-center justify-center cursor-pointer rounded-md hover:bg-[var(--fill-tsp-white-light)] !size-[32px] !rounded-[8px]"
          :title="presentation === 'dialog' ? t('Side view') : t('Center view')"
          @click="emit('toggle-presentation')"
          @keydown.enter.prevent="emit('toggle-presentation')">
          <SideViewIcon
            v-if="presentation === 'dialog'"
            :size="18"
            color="var(--icon-secondary)"
            class="!size-[18px] text-[var(--icon-secondary)]" />
          <CenterViewIcon
            v-else
            :size="18"
            color="var(--icon-secondary)"
            class="!size-[18px] text-[var(--icon-secondary)]" />
        </div>

        <div
          role="button"
          tabindex="0"
          class="flex h-7 w-7 items-center justify-center cursor-pointer rounded-md hover:bg-[var(--fill-tsp-white-light)] !size-[32px] !rounded-[8px]"
          :title="t('Close')"
          @click="hide"
          @keydown.enter.prevent="hide">
          <X :size="18" class="!size-[18px] text-[var(--icon-secondary)]" />
        </div>
      </div>
    </div>

    <!-- ManusComputerPanel -->
    <div class="flex-1 min-h-0">
      <component
        v-if="toolInfo?.view"
        :is="toolInfo.view"
        :live="live"
        :sessionId="sessionId"
        :toolContent="toolContent"
        :isShare="isShare" />
      <ComputerInactiveEmpty v-else />
    </div>

    <!-- ManusComputerTimeline -->
    <div
      class="mt-auto flex h-[45px] w-full items-center gap-[8px] py-[12px] ps-[16px] pe-[8px] relative bg-[var(--background-gray-main)] border-t border-b border-[var(--border-main)]">
      <div class="flex shrink-0 items-center gap-[8px]" dir="ltr">
        <button
          type="button"
          class="flex size-[24px] items-center justify-center text-[var(--icon-secondary)] transition-colors"
          :class="canGoPrev ? 'clickable cursor-pointer hover:text-[var(--icon-blue)]' : 'opacity-50 cursor-not-allowed'"
          :disabled="!canGoPrev"
          :title="t('Previous')"
          @click="goPrev">
          <SkipBack :size="16" />
        </button>
        <button
          type="button"
          class="flex size-[24px] items-center justify-center text-[var(--icon-secondary)] transition-colors"
          :class="canGoNext ? 'clickable cursor-pointer hover:text-[var(--icon-blue)]' : 'opacity-50 cursor-not-allowed'"
          :disabled="!canGoNext"
          :title="t('Next')"
          @click="goNext">
          <SkipForward :size="16" />
        </button>
      </div>

      <div
        class="group relative flex h-[4px] min-w-0 flex-1 cursor-pointer select-none items-center hover:z-10"
        @click="seekByClick"
        @mousedown="startScrub"
        @mousemove="onSliderHover"
        @mouseleave="hoverTooltip = false">
        <div class="absolute inset-x-0 h-[4px] rounded-full bg-[var(--fill-tsp-gray-dark)]" />
        <div
          class="absolute left-0 h-[4px] rounded-full bg-[var(--text-blue)]"
          :class="{ 'transition-[width]': !isScrubbing }"
          :style="{ width: `${progressPercent}%` }" />
        <div
          class="absolute top-1/2 size-[14px] -translate-y-1/2 -translate-x-1/2 rounded-full border-2 border-[var(--background-menu-white)] bg-[var(--text-blue)] drop-shadow-[0px_1px_4px_rgba(0,0,0,0.06)]"
          :style="{ left: `${progressPercent}%` }" />
        <div
          v-if="hoverTooltip"
          class="pointer-events-none absolute -top-10 z-20 flex h-[28px] items-center rounded bg-[var(--text-blue)] px-[10px] text-xs text-[var(--text-white)] whitespace-nowrap -translate-x-1/2"
          :style="{ left: `${hoverPercent}%` }">
          {{ hoverTimeLabel }}
        </div>
      </div>

      <div
        class="flex h-full shrink-0 items-center justify-center gap-[4px] px-[7px]"
        :class="realTime ? 'cursor-default' : 'cursor-pointer'"
        @click="!realTime && jumpToRealTime()">
        <div
          class="size-[6px] rounded-full"
          :class="(live || realTime) ? 'bg-[var(--function-success)]' : 'bg-[var(--text-tertiary)]'" />
        <span
          class="text-[12px] font-[500]"
          :class="(live || realTime) ? 'text-[var(--text-primary)]' : 'text-[var(--text-tertiary)]'">
          {{ $t('Live') }}
        </span>
      </div>

      <!-- Floating Jump to live -->
      <button
        v-if="!realTime"
        type="button"
        class="h-10 px-3 border border-[var(--border-main)] flex items-center gap-1 bg-[var(--background-menu-white)] hover:bg-[var(--background-gray-main)] shadow-[0px_5px_16px_0px_var(--shadow-S),0px_0px_1.25px_0px_var(--shadow-S)] rounded-full cursor-pointer absolute left-[50%] translate-x-[-50%]"
        style="bottom: calc(100% + 10px)"
        @click="jumpToRealTime">
        <PlayIcon :size="16" class="text-[var(--text-primary)]" />
        <span class="text-[var(--text-primary)] text-sm font-medium">{{ $t('Jump to live') }}</span>
      </button>
    </div>

    <!-- ManusComputerPlanner -->
    <PlanPanel v-if="plan && plan.steps.length > 0" :plan="plan" />
  </div>
</template>

<script setup lang="ts">
import { toRef, ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useMediaQuery } from '@vueuse/core';
import { useI18n } from 'vue-i18n';
import {
  PlayIcon, X, Monitor,
  SkipBack, SkipForward,
} from 'lucide-vue-next';
import type { ToolContent } from '@/types/message';
import type { PlanEventData } from '@/types/event';
import { useToolInfo } from '@/composables/useTool';
import PlanPanel from './PlanPanel.vue';
import ComputerInactiveEmpty from './ComputerInactiveEmpty.vue';
import CenterViewIcon from './icons/CenterViewIcon.vue';
import SideViewIcon from './icons/SideViewIcon.vue';

const props = withDefaults(defineProps<{
  sessionId?: string;
  realTime: boolean;
  toolContent: ToolContent;
  live: boolean;
  isShare: boolean;
  toolHistory?: ToolContent[];
  plan?: PlanEventData | null;
  presentation?: 'sidebar' | 'dialog';
}>(), {
  toolHistory: () => [],
  plan: null,
  presentation: 'sidebar',
});

const { t, locale } = useI18n();
const { toolInfo } = useToolInfo(toRef(props, 'toolContent'));
const isMobile = useMediaQuery('(max-width: 767px)');

/** Official ManusComputer root cn(sidebar|dialog) + mobile border-none */
const shellClass = computed(() => {
  if (props.presentation === 'dialog') {
    return 'rounded-[12px] border border-[var(--border-main)] bg-[var(--background-gray-main)] shadow-[0_24px_24px_-12px_var(--shadow-S),_0_0_0_1px_var(--shadow-M),_0_1px_1px_-0.5px_var(--shadow-M),_0_3px_3px_-1.5px_var(--shadow-M),_0_6px_6px_-3px_var(--shadow-M),_0_12px_12px_-6px_var(--shadow-S),_0_48px_48px_-24px_var(--shadow-XS),_0_10px_20px_1px_var(--shadow-S)]';
  }
  return isMobile.value ? 'border-none' : 'border-l border-[var(--border-main)]';
});

const isScrubbing = ref(false);
const showUseComputer = ref(false);
const useComputerRef = ref<HTMLElement | null>(null);
const hoverTooltip = ref(false);
const hoverPercent = ref(0);
const hoverTs = ref(0);
/** Absolute playhead in Unix seconds (manual / replay). Ignored while realTime. */
const playheadTs = ref(0);
/** Wall-clock tick so live end / playhead can advance in real time. */
const nowSec = ref(Math.floor(Date.now() / 1000));
let clockTimer: ReturnType<typeof setInterval> | null = null;

const isStreamingAction = computed(() => props.toolContent?.status === 'calling');

const usingLabel = computed(() => {
  if (!toolInfo.value) return t('Waiting for instructions');
  return `${t('Manus is using')} ${toolInfo.value.name}`;
});

const actionLabel = computed(() => {
  if (!toolInfo.value) return t('Waiting for instructions');
  const arg = toolInfo.value.functionArg;
  return arg ? `${toolInfo.value.function} ${arg}` : toolInfo.value.function;
});

const useComputerTitle = computed(() => t("Use {product}'s computer", { product: 'Manus' }));

const hoverTimeLabel = computed(() => {
  const d = new Date(hoverTs.value * 1000);
  try {
    return new Intl.DateTimeFormat(locale.value === 'zh' ? 'zh-CN' : 'en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(d);
  } catch {
    return d.toLocaleString();
  }
});

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
  (e: 'useComputer'): void;
  (e: 'toggle-presentation'): void;
}>();

const hide = () => emit('hide');
const jumpToRealTime = () => {
  playheadTs.value = timelineEnd.value;
  emit('jumpToRealTime');
};

const confirmUseComputer = () => {
  showUseComputer.value = false;
  emit('useComputer');
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
  const tool = history.value[currentIndex.value - 1];
  playheadTs.value = toUnixSec(tool.timestamp);
  emit('selectTool', tool);
};

const goNext = () => {
  if (!canGoNext.value) return;
  const tool = history.value[currentIndex.value + 1];
  playheadTs.value = toUnixSec(tool.timestamp);
  emit('selectTool', tool);
};

const seekToClientX = (clientX: number, el: HTMLElement) => {
  const rect = el.getBoundingClientRect();
  const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
  const t = timelineStart.value + ratio * timelineDuration.value;
  selectAtPlayhead(t);
};

const seekByClick = (event: MouseEvent) => {
  const el = event.currentTarget as HTMLElement;
  isScrubbing.value = true;
  seekToClientX(event.clientX, el);
  requestAnimationFrame(() => {
    isScrubbing.value = false;
  });
};

const onSliderHover = (event: MouseEvent) => {
  const el = event.currentTarget as HTMLElement;
  const rect = el.getBoundingClientRect();
  const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
  hoverPercent.value = ratio * 100;
  hoverTs.value = timelineStart.value + ratio * timelineDuration.value;
  hoverTooltip.value = true;
};

const startScrub = (event: MouseEvent) => {
  event.preventDefault();
  const el = event.currentTarget as HTMLElement;
  isScrubbing.value = true;
  seekToClientX(event.clientX, el);

  const onMove = (e: MouseEvent) => seekToClientX(e.clientX, el);
  const onUp = () => {
    isScrubbing.value = false;
    window.removeEventListener('mousemove', onMove);
    window.removeEventListener('mouseup', onUp);
  };
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);
};

watch(() => props.toolContent, (tool) => {
  if (!props.realTime && tool) {
    playheadTs.value = toUnixSec(tool.timestamp);
  }
});

watch(
  () => props.realTime,
  (rt) => {
    if (rt) {
      playheadTs.value = timelineEnd.value;
    } else if (props.toolContent) {
      playheadTs.value = toUnixSec(props.toolContent.timestamp);
    }
  },
);

const handleClickOutside = (event: MouseEvent) => {
  if (showUseComputer.value && useComputerRef.value && !useComputerRef.value.contains(event.target as Node)) {
    showUseComputer.value = false;
  }
};

const handleKeydown = (event: KeyboardEvent) => {
  const root = document.getElementById('manus-agent-workspace');
  if (!root) return;
  const sel = window.getSelection();
  const end = sel && sel.rangeCount > 0 ? sel.getRangeAt(0).endContainer : null;
  if (!end || !root.contains(end)) return;
  if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
    event.preventDefault();
    goPrev();
  } else if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
    event.preventDefault();
    goNext();
  }
};

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside);
  document.addEventListener('keydown', handleKeydown);
  playheadTs.value = props.toolContent
    ? toUnixSec(props.toolContent.timestamp)
    : timelineEnd.value;
  clockTimer = setInterval(() => {
    nowSec.value = Math.floor(Date.now() / 1000);
  }, 250);
});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside);
  document.removeEventListener('keydown', handleKeydown);
  if (clockTimer) {
    clearInterval(clockTimer);
    clockTimer = null;
  }
});
</script>
