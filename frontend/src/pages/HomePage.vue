<template>
  <SimpleBar>
    <div
      class="flex flex-col h-full flex-1 min-w-0 mx-auto w-full sm:min-w-[390px] px-5 justify-center items-start gap-2 relative max-w-full sm:max-w-full">
      <!-- Top header — same Manus / Agent·Lite switcher chrome as ChatPage -->
      <div class="w-[calc(100%+40px)] -mx-5 bg-[var(--background-gray-main)] sticky top-0 z-10 ps-[14px] pe-[20px] py-[12px] border-b border-transparent">
        <div class="flex justify-between items-center w-full">
          <div class="relative z-20 items-center flex-shrink-0 flex">
            <div class="flex items-center pointer-events-auto relative" ref="modeMenuRef">
              <button
                type="button"
                class="flex h-8 pt-[7px] md:pr-[6px] pr-[4px] pb-[7px] md:pl-[8px] pl-[6px] justify-center items-center gap-1 rounded-[8px] clickable hover:bg-[var(--fill-tsp-white-light)]"
                :aria-expanded="showModeMenu"
                aria-haspopup="menu"
                @click="toggleModeMenu">
                <span class="text-[var(--text-primary)] md:text-[18px] text-[16px] font-[500] md:leading-[22px] leading-[20px] truncate">Manus</span>
                <span
                  v-if="taskMode === 'chat'"
                  class="text-[var(--text-tertiary)] text-xs flex h-5 py-0.5 px-1.5 items-center rounded-[6px] border border-[var(--border-dark)] flex-shrink-0">
                  Lite
                </span>
                <ChevronDown class="size-3.5 text-[var(--icon-tertiary)] shrink-0" :size="14" />
              </button>
            </div>
          </div>
          <!-- Teleport: SimpleBar / overflow ancestors clip in-flow absolute menus -->
          <Teleport to="body">
            <div
              v-if="showModeMenu"
              ref="modeMenuPanelRef"
              role="menu"
              class="fixed z-[1100] min-w-[180px] rounded-[12px] border border-[var(--border-light)] bg-[var(--background-menu-white)] shadow-[0px_8px_32px_0px_var(--shadow-S)] p-1"
              :style="{ top: `${modeMenuPos.top}px`, left: `${modeMenuPos.left}px` }">
              <button
                type="button"
                role="menuitem"
                class="flex w-full items-center justify-between gap-2 px-3 py-2 rounded-[8px] text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
                @click="setTaskMode('agent')">
                <span>{{ t('Agent') }}</span>
                <Check v-if="taskMode === 'agent'" :size="16" class="text-[var(--icon-primary)]" />
              </button>
              <button
                type="button"
                role="menuitem"
                class="flex w-full items-center justify-between gap-2 px-3 py-2 rounded-[8px] text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
                @click="setTaskMode('chat')">
                <span>{{ t('Chat') }} · Lite</span>
                <Check v-if="taskMode === 'chat'" :size="16" class="text-[var(--icon-primary)]" />
              </button>
            </div>
          </Teleport>
          <div class="flex items-center gap-2">
            <a v-if="showGithubButton"
               :href="githubRepositoryUrl"
               target="_blank"
               rel="noopener noreferrer"
               class="clickable hidden sm:flex h-8 items-center justify-center gap-1 rounded-[8px] border border-[var(--border-main)] ps-2 pe-3 text-[14px] font-medium leading-[20px] tracking-[-0.15px] text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
               title="Visit GitHub Repository">
              <Github :size="16" />
              GitHub
            </a>
          </div>
        </div>
      </div>
      <div class="max-md:px-[16px] mx-auto w-full max-w-full sm:max-w-[768px] sm:min-w-[360px] mt-[20vh] mb-auto">
        <div class="w-full flex pl-4 items-center justify-start pb-4">
          <span class="text-[var(--text-primary)] text-start font-serif text-[32px] leading-[40px]">
            {{ $t('Hello') }}, {{ currentUser?.fullname }}
            <br />
            <span class="text-[var(--text-tertiary)]">
              {{ $t('What can I do for you?') }}
            </span>
          </span>
        </div>
        <div class="flex flex-col gap-1 w-full">
          <div class="flex flex-col w-full bg-[var(--background-gray-main)]">
            <div class="[&amp;:not(:empty)]:pb-2 bg-[var(--background-gray-main)] rounded-[22px_22px_0px_0px]">
            </div>
            <ChatBox :rows="2" v-model="message" v-model:attachments="attachments" @submit="handleSubmit"
              :isRunning="false" />
          </div>
        </div>
        <!-- Suggestion chips (structure replicated from manus.im home) -->
        <div class="relative w-full">
          <div class="w-full transition-transform duration-300 ease-out relative mt-[20px]">
            <div class="w-full flex flex-col justify-center items-center gap-4">
              <div class="flex flex-wrap justify-center items-center gap-2">
                <div v-for="suggestion in visibleSuggestions" :key="suggestion.label" role="button" tabindex="0"
                  class="h-10 px-[14px] py-[7px] rounded-full border border-[var(--border-main)] flex justify-center items-center gap-2 clickable cursor-pointer hover:bg-[var(--fill-tsp-white-light)] flex-shrink-0"
                  @click="handleSuggestionClick(suggestion)">
                  <component :is="suggestion.icon" :size="18" color="var(--icon-tertiary)" />
                  <div class="flex justify-start items-center gap-1">
                    <span class="text-[var(--text-primary)] text-[14px] font-normal">{{ $t(suggestion.label) }}</span>
                  </div>
                </div>
                <div v-if="!showMoreSuggestions" role="button" tabindex="0"
                  class="h-10 px-[14px] text-sm py-[7px] rounded-full border border-[var(--border-main)] flex justify-center items-center gap-2 clickable cursor-pointer hover:bg-[var(--fill-tsp-white-light)] flex-shrink-0 text-[var(--text-primary)]"
                  @click="showMoreSuggestions = true">
                  {{ $t('More') }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </SimpleBar>
</template>

<script setup lang="ts">
import SimpleBar from '../components/SimpleBar.vue';
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ChatBox from '../components/ChatBox.vue';
import { createSession, updateSessionTaskMode } from '../api/agent';
import { showErrorToast } from '../utils/toast';
import {
  Github, Presentation, Globe, Palette, Gamepad2,
  Telescope, ChartColumn, Image, FileText, ChevronDown, Check,
} from 'lucide-vue-next';
import type { Component } from 'vue';
import type { FileInfo } from '../api/file';
import { useFilePreviewer } from '../composables/useFilePreviewer';
import { useAuth } from '../composables/useAuth';
import { getCachedClientConfig } from '../api/config';

const { t } = useI18n();
const router = useRouter();
const message = ref('');
const isSubmitting = ref(false);
const attachments = ref<FileInfo[]>([]);
const { hideFilePreviewer } = useFilePreviewer();
const { currentUser } = useAuth();
const showGithubButton = ref(false);
const githubRepositoryUrl = ref('https://github.com/simpleyyt/ai-manus');

const taskMode = ref<'agent' | 'chat'>('agent');
const showModeMenu = ref(false);
const modeMenuRef = ref<HTMLElement | null>(null);
const modeMenuPanelRef = ref<HTMLElement | null>(null);
const modeMenuPos = ref({ top: 0, left: 0 });

const toggleModeMenu = () => {
  if (!showModeMenu.value && modeMenuRef.value) {
    const r = modeMenuRef.value.getBoundingClientRect();
    modeMenuPos.value = { top: r.bottom + 6, left: r.left };
  }
  showModeMenu.value = !showModeMenu.value;
};

const setTaskMode = (mode: 'agent' | 'chat') => {
  showModeMenu.value = false;
  taskMode.value = mode;
};

const handleModeMenuOutside = (e: MouseEvent) => {
  if (!showModeMenu.value) return;
  const t = e.target as Node;
  if (modeMenuRef.value?.contains(t) || modeMenuPanelRef.value?.contains(t)) return;
  showModeMenu.value = false;
};

const handleModeMenuScroll = () => {
  if (showModeMenu.value) showModeMenu.value = false;
};

// Suggestion chips, structure replicated from the manus.im home page
interface Suggestion {
  label: string;
  icon: Component;
}

const primarySuggestions: Suggestion[] = [
  { label: 'Create slides', icon: Presentation },
  { label: 'Build website', icon: Globe },
  { label: 'Design', icon: Palette },
  { label: 'Create games', icon: Gamepad2 },
];

const moreSuggestions: Suggestion[] = [
  { label: 'Deep research', icon: Telescope },
  { label: 'Analyze data', icon: ChartColumn },
  { label: 'Generate image', icon: Image },
  { label: 'Write report', icon: FileText },
];

const showMoreSuggestions = ref(false);

const visibleSuggestions = computed(() =>
  showMoreSuggestions.value ? [...primarySuggestions, ...moreSuggestions] : primarySuggestions
);

const handleSuggestionClick = (suggestion: Suggestion) => {
  message.value = t(suggestion.label);
};

onMounted(async () => {
  hideFilePreviewer();
  document.addEventListener('mousedown', handleModeMenuOutside);
  window.addEventListener('scroll', handleModeMenuScroll, true);
  const clientConfig = await getCachedClientConfig();
  if (clientConfig) {
    showGithubButton.value = clientConfig.show_github_button;
    githubRepositoryUrl.value = clientConfig.github_repository_url;
  }
});

onUnmounted(() => {
  document.removeEventListener('mousedown', handleModeMenuOutside);
  window.removeEventListener('scroll', handleModeMenuScroll, true);
});

const handleSubmit = async () => {
  if (message.value.trim() && !isSubmitting.value) {
    isSubmitting.value = true;

    try {
      const session = await createSession();
      const sessionId = session.session_id;
      if (taskMode.value === 'chat') {
        await updateSessionTaskMode(sessionId, 'chat');
      }

      router.push({
        path: `/chat/${sessionId}`,
        state: {
          message: message.value,
          taskMode: taskMode.value,
          files: attachments.value.map((file: FileInfo) => ({
            file_id: file.file_id,
            filename: file.filename,
            content_type: file.content_type,
            size: file.size,
            upload_date: file.upload_date
          }))
        }
      });
    } catch (error) {
      console.error('Failed to create session:', error);
      showErrorToast(t('Failed to create session, please try again later'));
      isSubmitting.value = false;
    }
  }
};
</script>
