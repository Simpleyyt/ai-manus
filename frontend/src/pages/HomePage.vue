<template>
  <SimpleBar
    class="[&_.simplebar-scrollbar]:opacity-0
      [&_.simplebar-scrollbar::before]:bg-[var(--text-disable)]
      [&:hover_.simplebar-scrollbar]:opacity-100
      [&:hover_.simplebar-scrollbar::before]:bg-[var(--text-tertiary)]
      [&_.simplebar-scrollbar::before]:w-[6px]"
    style="--simplebar-scrollbar-width: 6px;">
    <div
      class="flex flex-col h-full flex-1 min-w-0 mx-auto w-full sm:min-w-[390px] px-5 justify-center items-start gap-2 relative max-w-full sm:max-w-full">
      <div class="w-full pt-4 pb-4 px-5 bg-[var(--background-gray-main)] sticky top-0 z-10 mx-[-1.25]">
        <!-- Loading Progress Indicator -->
        <div v-if="isSubmitting"
          class="absolute top-0 left-0 w-full h-[3px] z-[10]
          overflow-hidden pointer-events-none">
          <div class="h-full bg-[var(--text-blue)] transition-all duration-300 ease-out
            animate-pulse"
            style="width: 100%; box-shadow: 0 0 10px var(--text-blue);">
          </div>
        </div>
        <div class="flex justify-between items-center w-full absolute left-0 right-0">
          <div class="h-8 relative z-20 overflow-hidden flex gap-2 items-center flex-shrink-0">
            <div class="relative flex items-center">
              <div @click="toggleLeftPanel" v-if="!isLeftPanelShow"
                class="flex h-7 w-7 items-center justify-center cursor-pointer rounded-md
                hover:bg-[var(--fill-tsp-gray-main)]
                transition-colors hover:opacity-90 active:opacity-80 duration-100">
                <PanelLeft class="size-5 text-[var(--icon-secondary)]" />
              </div>
            </div>
            <div class="flex">
              <Bot :size="30" />
              <ManusLogoTextIcon />
            </div>
          </div>
          <div class="flex items-center gap-2">
            <div class="relative flex items-center" aria-expanded="false" aria-haspopup="dialog"
              @mouseenter="handleUserMenuEnter" @mouseleave="handleUserMenuLeave">
              <div class="relative flex items-center justify-center font-bold cursor-pointer
                flex-shrink-0 transition-opacity duration-100 hover:opacity-90">
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
      <div class="w-full max-w-full sm:max-w-[768px] sm:min-w-[390px] mx-auto mt-[180px] mb-auto">
        <div class="w-full flex pl-4 items-center justify-start pb-4">
          <span class="text-[var(--text-primary)] text-start text-[32px]
            leading-[40px] font-[500] tracking-[-0.5px]"
            :style="{ fontFamily: 'ui-serif, Georgia, Cambria, Times, serif' }">
            {{ $t('Hello') }}, {{ currentUser?.fullname }}
            <br />
            <span class="text-[var(--text-tertiary)] tracking-[-0.3px]">
              {{ $t('What can I do for you?') }}
            </span>
          </span>
        </div>
        <div class="flex flex-col gap-1 w-full">
          <div class="flex flex-col bg-gradient-to-br
            from-[var(--background-gray-main)] to-[var(--background-card-gray)]
            w-full rounded-t-[22px]">
            <div class="[&amp;:not(:empty)]:pb-2 bg-transparent rounded-[22px_22px_0px_0px]">
            </div>
            <ChatBox :rows="2" v-model="message" @submit="handleSubmit" :isRunning="false" :attachments="attachments" />
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
import { Bot, PanelLeft } from 'lucide-vue-next';
import ManusLogoTextIcon from '../components/icons/ManusLogoTextIcon.vue';
import type { FileInfo } from '../api/file';
import { useLeftPanel } from '../composables/useLeftPanel';
import { useFilePanel } from '../composables/useFilePanel';
import { useAuth } from '../composables/useAuth';
import UserMenu from '../components/UserMenu.vue';

const { t } = useI18n();
const router = useRouter();
const message = ref('');
const isSubmitting = ref(false);
const attachments = ref<FileInfo[]>([]);
const { toggleLeftPanel, isLeftPanelShow } = useLeftPanel();
const { hideFilePanel } = useFilePanel();
const { currentUser } = useAuth();

// Get first letter of user's fullname for avatar display
const avatarLetter = computed(() => {
  return currentUser.value?.fullname?.charAt(0)?.toUpperCase() || 'M';
});

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
  userMenuTimeout.value = setTimeout(() => {
    showUserMenu.value = false;
  }, 200); // 200ms delay to allow moving to menu
};

onMounted(() => {
  hideFilePanel();
})

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
