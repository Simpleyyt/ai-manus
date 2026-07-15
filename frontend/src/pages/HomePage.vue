<template>
  <SimpleBar>
    <div
      class="flex flex-col h-full flex-1 min-w-0 mx-auto w-full sm:min-w-[390px] px-5 justify-center items-start gap-2 relative max-w-full sm:max-w-full">
      <div class="w-full pt-4 pb-4 px-5 bg-[var(--background-gray-main)] sticky top-0 z-10 mx-[-1.25]">
        <div class="flex justify-end items-center w-full absolute left-0 right-0">
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
          </div>
        </div>
        <div class="h-8"></div>
      </div>
      <div class="max-md:px-[16px] mx-auto w-full max-w-full sm:max-w-[768px] sm:min-w-[360px] mt-[20vh] mb-auto">
        <div class="w-full flex pl-4 items-center justify-start pb-4">
          <span class="text-[var(--text-primary)] text-start font-serif text-[32px] leading-[40px]" :style="{
            fontFamily:
              'ui-serif, Georgia, Cambria, &quot;Times New Roman&quot;, Times, serif',
          }">
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
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ChatBox from '../components/ChatBox.vue';
import { createSession } from '../api/agent';
import { showErrorToast } from '../utils/toast';
import {
  Github, Presentation, Globe, Palette, Gamepad2,
  Telescope, ChartColumn, Image, FileText
} from 'lucide-vue-next';
import type { Component } from 'vue';
import type { FileInfo } from '../api/file';
import { useFilePanel } from '../composables/useFilePanel';
import { useAuth } from '../composables/useAuth';
import { getCachedClientConfig } from '../api/config';

const { t } = useI18n();
const router = useRouter();
const message = ref('');
const isSubmitting = ref(false);
const attachments = ref<FileInfo[]>([]);
const { hideFilePanel } = useFilePanel();
const { currentUser } = useAuth();
const showGithubButton = ref(false);
const githubRepositoryUrl = ref('https://github.com/simpleyyt/ai-manus');

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
