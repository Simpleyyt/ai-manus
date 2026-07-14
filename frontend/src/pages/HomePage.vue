<template>
  <SimpleBar>
    <div
      class="flex flex-col h-full flex-1 min-w-0 mx-auto w-full sm:min-w-[390px] px-5 justify-center items-start gap-2 relative max-w-full sm:max-w-full">
      <div class="w-full pt-4 pb-4 px-5 bg-[var(--background-gray-main)] sticky top-0 z-10 mx-[-1.25]">
        <div class="flex justify-between items-center w-full absolute left-0 right-0">
          <div class="h-8 relative z-20 overflow-hidden flex gap-2 items-center flex-shrink-0">
            <div class="relative flex items-center">
              <div @click="toggleLeftPanel" v-if="!isLeftPanelShow"
                class="flex h-7 w-7 items-center justify-center cursor-pointer rounded-md hover:bg-[var(--fill-tsp-gray-main)]">
                <PanelLeft class="size-5 text-[var(--icon-secondary)]" />
              </div>
            </div>
            <div class="flex">
              <Bot :size="30" />
              <ManusLogoTextIcon />
            </div>
          </div>
          <div class="flex items-center gap-2">
            <a v-if="showGithubButton"
               :href="githubRepositoryUrl"
               target="_blank"
               rel="noopener noreferrer"
               class="items-center justify-center whitespace-nowrap font-medium transition-colors hover:opacity-90 active:opacity-80 px-[12px] gap-[6px] text-sm min-w-16 outline outline-1 -outline-offset-1 hover:bg-[var(--fill-tsp-white-light)] text-[var(--text-primary)] outline-[var(--border-btn-main)] bg-transparent clickable hidden sm:flex rounded-[100px] relative h-[32px] group"
               title="Visit GitHub Repository">
              <Github class="size-[18px]" />
              GitHub
            </a>
            <div class="relative flex items-center" aria-expanded="false" aria-haspopup="dialog"
              @mouseenter="handleUserMenuEnter" @mouseleave="handleUserMenuLeave">
              <div class="relative flex items-center justify-center font-bold cursor-pointer flex-shrink-0">
                <div
                  class="relative flex items-center justify-center font-bold flex-shrink-0 rounded-full overflow-hidden"
                  style="width: 32px; height: 32px; font-size: 16px; color: rgba(255, 255, 255, 0.9); background-color: rgb(59, 130, 246);">
                  {{ avatarLetter }}</div>
              </div>
              <!-- User Menu -->
              <div v-if="showUserMenu" @mouseenter="handleUserMenuEnter" @mouseleave="handleUserMenuLeave"
                class="absolute top-full right-0 mt-1 mr-[-15px] z-50">
                <UserMenu />
              </div>
            </div>
          </div>
        </div>
        <div class="h-8"></div>
      </div>
      <div class="w-full max-w-full sm:max-w-[680px] sm:min-w-[390px] mx-auto mt-auto mb-auto pb-[8vh]">
        <div class="w-full flex flex-col items-center justify-center pb-8 gap-1">
          <span v-if="greetingName" class="text-[var(--text-tertiary)] text-center font-serif text-[22px] leading-[30px]"
            :style="{ fontFamily: serifFontFamily }">
            {{ $t('Hello') }}, {{ greetingName }}
          </span>
          <h1 class="text-[var(--text-primary)] text-center font-serif text-[36px] leading-[46px] sm:text-[40px] sm:leading-[52px]"
            :style="{ fontFamily: serifFontFamily }">
            {{ $t('What can I do for you?') }}
          </h1>
        </div>
        <div class="flex flex-col gap-1 w-full">
          <div class="flex flex-col bg-[var(--background-gray-main)] w-full">
            <div class="[&amp;:not(:empty)]:pb-2 bg-[var(--background-gray-main)] rounded-[22px_22px_0px_0px]">
            </div>
            <ChatBox ref="chatBoxRef" :rows="2" v-model="message" v-model:attachments="attachments" @submit="handleSubmit"
              :isRunning="false" />
          </div>
          <!-- Suggestion chips -->
          <div class="flex flex-wrap items-center justify-center gap-2 pt-2">
            <button v-for="chip in visibleChips" :key="chip.label" @click="handleChipClick(chip)"
              class="inline-flex items-center gap-[6px] h-[34px] px-[14px] rounded-full border border-[var(--border-btn-main)] bg-transparent text-[13px] text-[var(--text-secondary)] cursor-pointer transition-colors hover:bg-[var(--fill-tsp-white-light)] hover:text-[var(--text-primary)]">
              <component :is="chip.icon" :size="15" class="text-[var(--icon-secondary)]" />
              {{ $t(chip.label) }}
            </button>
            <button v-if="!showAllChips" @click="showAllChips = true"
              class="inline-flex items-center gap-[6px] h-[34px] px-[14px] rounded-full border border-[var(--border-btn-main)] bg-transparent text-[13px] text-[var(--text-secondary)] cursor-pointer transition-colors hover:bg-[var(--fill-tsp-white-light)] hover:text-[var(--text-primary)]">
              {{ $t('More') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </SimpleBar>
</template>

<script setup lang="ts">
import SimpleBar from '../components/SimpleBar.vue';
import { ref, onMounted, computed, type FunctionalComponent } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ChatBox from '../components/ChatBox.vue';
import { createSession } from '../api/agent';
import { showErrorToast } from '../utils/toast';
import {
  Bot, PanelLeft, Github, Presentation, Globe, Palette,
  Gamepad2, ChartColumn, FileText, Search, Table,
} from 'lucide-vue-next';
import ManusLogoTextIcon from '../components/icons/ManusLogoTextIcon.vue';
import type { FileInfo } from '../api/file';
import { useLeftPanel } from '../composables/useLeftPanel';
import { useFilePanel } from '../composables/useFilePanel';
import { useAuth } from '../composables/useAuth';
import { getCachedClientConfig } from '../api/config';
import UserMenu from '../components/UserMenu.vue';

const { t } = useI18n();
const router = useRouter();
const message = ref('');
const isSubmitting = ref(false);
const attachments = ref<FileInfo[]>([]);
const { toggleLeftPanel, isLeftPanelShow } = useLeftPanel();
const { hideFilePanel } = useFilePanel();
const { currentUser } = useAuth();
const showGithubButton = ref(false);
const githubRepositoryUrl = ref('https://github.com/simpleyyt/ai-manus');
const chatBoxRef = ref<InstanceType<typeof ChatBox> | null>(null);

const serifFontFamily = 'ui-serif, Georgia, Cambria, "Times New Roman", Times, serif';

// Get first letter of user's fullname for avatar display
const avatarLetter = computed(() => {
  return currentUser.value?.fullname?.charAt(0)?.toUpperCase() || 'M';
});

const greetingName = computed(() => currentUser.value?.fullname || '');

// Suggestion chips shown below the input box
interface SuggestionChip {
  label: string;
  prompt: string;
  icon: FunctionalComponent;
}

const primaryChips: SuggestionChip[] = [
  { label: 'Create slides', prompt: 'Create slides prompt', icon: Presentation },
  { label: 'Build website', prompt: 'Build website prompt', icon: Globe },
  { label: 'Design', prompt: 'Design prompt', icon: Palette },
  { label: 'Create games', prompt: 'Create games prompt', icon: Gamepad2 },
];

const extraChips: SuggestionChip[] = [
  { label: 'Analyze data', prompt: 'Analyze data prompt', icon: ChartColumn },
  { label: 'Research', prompt: 'Research prompt', icon: Search },
  { label: 'Write report', prompt: 'Write report prompt', icon: FileText },
  { label: 'Create spreadsheet', prompt: 'Create spreadsheet prompt', icon: Table },
];

const showAllChips = ref(false);
const visibleChips = computed(() =>
  showAllChips.value ? [...primaryChips, ...extraChips] : primaryChips
);

const handleChipClick = (chip: SuggestionChip) => {
  message.value = t(chip.prompt);
  chatBoxRef.value?.focus();
};

// User menu state
const showUserMenu = ref(false);
const userMenuTimeout = ref<number | null>(null);

// Show user menu on hover
const handleUserMenuEnter = () => {
  if (userMenuTimeout.value) {
    clearTimeout(userMenuTimeout.value);
    userMenuTimeout.value = null;
  }
  showUserMenu.value = true;
};

// Hide user menu with delay
const handleUserMenuLeave = () => {
  userMenuTimeout.value = window.setTimeout(() => {
    showUserMenu.value = false;
  }, 200); // 200ms delay to allow moving to menu
};

onMounted(async () => {
  hideFilePanel();
  const clientConfig = await getCachedClientConfig();
  if (clientConfig) {
    showGithubButton.value = clientConfig.show_github_button;
    githubRepositoryUrl.value = clientConfig.github_repository_url;
  }
});

const handleSubmit = async () => {
  if (message.value.trim() && !isSubmitting.value) {
    isSubmitting.value = true;

    try {
      // Create new Agent
      const session = await createSession();
      const sessionId = session.session_id;

      // Navigate to new route with session_id, passing initial message via state
      router.push({
        path: `/chat/${sessionId}`,
        state: {
          message: message.value, files: attachments.value.map((file: FileInfo) => ({
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
