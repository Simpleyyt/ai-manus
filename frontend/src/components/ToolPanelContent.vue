<template>
  <div class="bg-[var(--background-gray-main)] sm:bg-[var(--background-menu-white)] sm:rounded-[22px] shadow-[0px_0px_8px_0px_rgba(0,0,0,0.02)] border border-black/8 dark:border-[var(--border-light)] flex h-full w-full">
    <div class="flex-1 min-w-0 p-4 flex flex-col h-full">
      <!-- Header aligned with Manus "Manus's Computer" panel -->
      <div class="flex items-center gap-2 w-full">
        <div class="text-[var(--text-primary)] text-lg font-semibold flex-1 truncate">{{ $t("Manus's Computer") }}</div>
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
            class="absolute right-0 top-[calc(100%+6px)] z-50 min-w-[180px] rounded-[12px] border border-[var(--border-light)] bg-[var(--background-menu-white)] shadow-[0px_8px_32px_0px_var(--shadow-S)] py-1">
            <div class="px-3 py-1.5 text-[12px] text-[var(--text-tertiary)]">{{ t('Select an application to use') }}</div>
            <button type="button"
              class="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--fill-tsp-white-main)]"
              :class="preferredApp === 'browser' ? 'text-[var(--text-primary)] font-medium' : 'text-[var(--text-secondary)]'"
              @click="selectApp('browser')">
              <Globe :size="16" />
              {{ t('Browser') }}
              <Check v-if="preferredApp === 'browser'" :size="16" class="ml-auto" />
            </button>
            <button type="button"
              class="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--fill-tsp-white-main)]"
              :class="preferredApp === 'terminal' ? 'text-[var(--text-primary)] font-medium' : 'text-[var(--text-secondary)]'"
              @click="selectApp('terminal')">
              <Terminal :size="16" />
              {{ t('Terminal') }}
              <Check v-if="preferredApp === 'terminal'" :size="16" class="ml-auto" />
            </button>
          </div>
        </div>
        <button
          type="button"
          class="w-7 h-7 relative rounded-md inline-flex items-center justify-center gap-2.5 cursor-pointer hover:bg-[var(--fill-tsp-gray-main)]"
          @click="hide">
          <Minimize2 class="w-5 h-5 text-[var(--icon-tertiary)]" />
        </button>
      </div>

      <div v-if="toolInfo" class="flex items-center gap-2 mt-2">
        <div
          class="w-[40px] h-[40px] bg-[var(--fill-tsp-gray-main)] rounded-lg flex items-center justify-center flex-shrink-0">
          <component :is="toolInfo.icon" :size="28" />
        </div>
        <div class="flex-1 flex flex-col gap-1 min-w-0">
          <div class="text-[12px] text-[var(--text-tertiary)]">{{ $t('Manus is using') }} <span
              class="text-[var(--text-secondary)]">{{ toolInfo.name }}</span></div>
          <div title="{{ toolInfo.function }} {{ toolInfo.functionArg }}"
            class="max-w-[100%] w-[max-content] truncate text-[13px] rounded-full inline-flex items-center px-[10px] py-[3px] border border-[var(--border-light)] bg-[var(--fill-tsp-gray-main)] text-[var(--text-secondary)]">
            {{ toolInfo.function }}<span
              class="flex-1 min-w-0 px-1 ml-1 text-[12px] font-mono max-w-full text-ellipsis overflow-hidden whitespace-nowrap text-[var(--text-tertiary)]"><code>{{ toolInfo.functionArg }}</code></span>
          </div>
        </div>
      </div>

      <div
        class="flex flex-col rounded-[12px] overflow-hidden bg-[var(--background-gray-main)] border border-[var(--border-dark)] dark:border-black/30 shadow-[0px_4px_32px_0px_rgba(0,0,0,0.04)] flex-1 min-h-0 mt-[16px]">
        <component v-if="toolInfo" :is="toolInfo.view" :live="live" :sessionId="sessionId"
          :toolContent="toolContent" :isShare="isShare" />

        <!-- Live / replay footer (Manus computer bottom bar) -->
        <div class="mt-auto flex w-full items-center gap-2 px-3 h-[44px] border-t border-[var(--border-light)] bg-[var(--background-menu-white)] relative">
          <button
            v-if="!realTime"
            type="button"
            class="h-8 px-3 border border-[var(--border-main)] flex items-center gap-1 bg-[var(--background-white-main)] hover:bg-[var(--background-gray-main)] shadow-[0px_5px_16px_0px_var(--shadow-S)] rounded-full cursor-pointer"
            @click="jumpToRealTime">
            <PlayIcon :size="14" />
            <span class="text-[var(--text-primary)] text-sm font-medium">{{ $t('Jump to live') }}</span>
          </button>
          <div class="flex-1" />
          <div class="flex items-center gap-1.5 text-[12px] text-[var(--text-tertiary)]">
            <span
              class="inline-block size-2 rounded-full"
              :class="live || realTime ? 'bg-[var(--function-success)]' : 'bg-[var(--icon-tertiary)]'" />
            {{ live || realTime ? t('live') : t('Replay') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toRef, ref, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { Minimize2, PlayIcon, Monitor, ChevronDown, Globe, Terminal, Check } from 'lucide-vue-next';
import type { ToolContent } from '@/types/message';
import { useToolInfo } from '@/composables/useTool';

const props = defineProps<{
  sessionId?: string;
  realTime: boolean;
  toolContent: ToolContent;
  live: boolean;
  isShare: boolean;
}>();

const { t } = useI18n();
const { toolInfo } = useToolInfo(toRef(props, 'toolContent'));

const showAppMenu = ref(false);
const appMenuRef = ref<HTMLElement | null>(null);
const preferredApp = ref<'browser' | 'terminal'>('browser');

const emit = defineEmits<{
  (e: 'jumpToRealTime'): void,
  (e: 'hide'): void
}>();

const hide = () => {
  emit('hide');
};

const jumpToRealTime = () => {
  emit('jumpToRealTime');
};

const selectApp = (app: 'browser' | 'terminal') => {
  preferredApp.value = app;
  showAppMenu.value = false;
};

const handleClickOutside = (event: MouseEvent) => {
  if (showAppMenu.value && appMenuRef.value && !appMenuRef.value.contains(event.target as Node)) {
    showAppMenu.value = false;
  }
};

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside);
  // Infer preferred app from current tool name
  const name = (toolInfo.value?.name || '').toLowerCase();
  if (name.includes('shell') || name.includes('terminal')) {
    preferredApp.value = 'terminal';
  } else {
    preferredApp.value = 'browser';
  }
});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside);
});
</script>
