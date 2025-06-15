<template>
  <div :class="isPanelShow ?
    'h-full flex flex-col' :
    'h-full flex flex-col fixed top-0 start-0 bottom-0 z-[1]'" :style="isPanelShow ?
      'width: 300px; transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);' :
      'width: 24px; transition: width 0.36s cubic-bezier(0.4, 0, 0.2, 1);'">
    <div :class="isHomepage ?
      'absolute start-0 top-0 w-[100vw] p-4 bg-[var(--background-gray-main)] pointer-events-none flex' :
      'absolute start-4 top-3 md:top-4 pointer-events-none flex'">
      <div class="flex items-center gap-2 pointer-events-auto">
        <div class="relative flex">
          <div
            class="flex h-7 w-7 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md"
            @click="togglePanel">
            <PanelRight class="h-5 w-5 text-[var(--icon-secondary)]" />
          </div>
        </div>
        <div v-if="isHomepage" class="flex">
          <Bot :size="30" />
          <ManusLogoTextIcon />
        </div>
      </div>
      <div>
      </div>
    </div>
    <div
      :class="isPanelShow ?
        'flex flex-col overflow-hidden bg-[var(--background-nav)] h-full opacity-100 translate-x-0' :
        'flex flex-col overflow-hidden bg-[var(--background-nav)] fixed top-1 start-1 bottom-1 z-[1] border-1 dark:border-[1px] border-[var(--border-main)] dark:border-[var(--border-light)] rounded-xl shadow-[0px_8px_32px_0px_rgba(0,0,0,0.16),0px_0px_0px_1px_rgba(0,0,0,0.06)] opacity-0 pointer-events-none -translate-x-10'"
      :style="(isPanelShow ? 'width: 300px;' : 'width: 0px;') + ' transition: opacity 0.2s, transform 0.2s, width 0.2s;'">
      <div class="flex">
        <div class="flex items-center px-3 py-3 flex-row h-[52px] gap-1 justify-end w-full">
          <div class="flex justify-between w-full px-1 pt-2">
            <div class="relative flex">
              <div
                class="flex h-7 w-7 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md"
                @click="togglePanel">
                <PanelRight class="h-5 w-5 text-[var(--icon-secondary)]" />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="px-3 mb-1 flex justify-center flex-shrink-0">
        <button @click="handleNewTaskClick"
          class="flex min-w-[36px] w-full items-center justify-center gap-1.5 rounded-lg h-[32px] bg-[var(--Button-primary-white)] hover:bg-white/20 dark:hover:bg-black/60 cursor-pointer shadow-[0px_0.5px_3px_0px_var(--shadow-S)]">
          <Plus class="h-4 w-4 text-[var(--icon-primary)]" />
          <span class="text-sm font-medium text-[var(--text-primary)] whitespace-nowrap truncate">
            {{ t('New Task') }}
          </span>
          <div class="flex items-center gap-0.5">
            <span
              class="flex text-[var(--text-tertiary)] justify-center items-center min-w-5 h-5 px-1 rounded-[4px] bg-[var(--fill-tsp-white-light)] border border-[var(--border-light)]">
              <Command :size="14" />
            </span>
            <span
              class="flex justify-center items-center w-5 h-5 px-1 rounded-[4px] bg-[var(--fill-tsp-white-light)] border border-[var(--border-light)] text-sm font-normal text-[var(--text-tertiary)] ">
              K
            </span>
          </div>
        </button>
      </div>
      <div v-if="sessions.length > 0" class="flex flex-col flex-1 min-h-0 overflow-auto pt-2 pb-5 overflow-x-hidden">
        <SessionItem v-for="session in sessions" :key="session.session_id" :session="session"
          @deleted="handleSessionDeleted" />
      </div>
      <div v-else class="flex flex-1 flex-col items-center justify-center gap-4">
        <div class="flex flex-col items-center gap-2 text-[var(--text-tertiary)]">
          <MessageSquareDashed :size="38" />
          <span class="text-sm font-medium">{{ t('Create a task to get started') }}</span></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PanelRight, Plus, Command, Bot, MessageSquareDashed } from 'lucide-vue-next';
import ManusLogoTextIcon from './icons/ManusLogoTextIcon.vue';
import SessionItem from './SessionItem.vue';
import { usePanelState } from '../composables/usePanelState';
import { computed, ref, onMounted, watch, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getSessionsSSE, getSessions } from '../api/agent';
import { ListSessionItem } from '../types/response';
import { useI18n } from 'vue-i18n';

const { t } = useI18n()
const { isPanelShow, togglePanel } = usePanelState()
const route = useRoute()
const router = useRouter()

// Check if current page is homepage
const isHomepage = computed(() => {
  return route.path === '/'
})

const sessions = ref<ListSessionItem[]>([])
const cancelGetSessionsSSE = ref<(() => void) | null>(null)

// Function to fetch sessions data
const updateSessions = async () => {
  try {
    const response = await getSessions()
    sessions.value = response.sessions
  } catch (error) {
    console.error('Failed to fetch sessions:', error)
  }
}

// Function to fetch sessions data
const fetchSessions = async () => {
  try {
    if (cancelGetSessionsSSE.value) {
      cancelGetSessionsSSE.value()
      cancelGetSessionsSSE.value = null
    }
    cancelGetSessionsSSE.value = await getSessionsSSE({
      onMessage: (event) => {
        sessions.value = event.data.sessions
      },
      onError: (error) => {
        console.error('Failed to fetch sessions:', error)
      }
    })
  } catch (error) {
    console.error('Failed to fetch sessions:', error)
  }
}

const handleNewTaskClick = () => {
  router.push('/')
}

const handleSessionDeleted = (sessionId: string) => {
  console.log('handleSessionDeleted', sessionId)
  sessions.value = sessions.value.filter(session => session.session_id !== sessionId);
}

// Handle keyboard shortcuts
const handleKeydown = (event: KeyboardEvent) => {
  // Check for Command + K (Mac) or Ctrl + K (Windows/Linux)
  if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
    event.preventDefault()
    handleNewTaskClick()
  }
}

onMounted(async () => {
  // Initial fetch of sessions
  fetchSessions()

  // Add keyboard event listener
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  if (cancelGetSessionsSSE.value) {
    cancelGetSessionsSSE.value()
    cancelGetSessionsSSE.value = null
  }

  // Remove keyboard event listener
  window.removeEventListener('keydown', handleKeydown)
})

watch(() => route.path, async () => {
  await updateSessions()
})
</script>
