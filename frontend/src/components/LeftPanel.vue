<template>
  <div :class="isLeftPanelShow ?
    'h-full flex flex-col' :
    'h-full flex flex-col fixed top-0 start-0 bottom-0 z-[1]'" :style="isLeftPanelShow ?
      'width: 300px; transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);' :
      'width: 24px; transition: width 0.36s cubic-bezier(0.4, 0, 0.2, 1);'">
    <div
      :class="isLeftPanelShow ?
        'flex flex-col overflow-hidden bg-[var(--background-nav)] h-full opacity-100 translate-x-0' :
        'flex flex-col overflow-hidden bg-[var(--background-nav)] fixed top-1 start-1 bottom-1 z-[1] border-1 dark:border-[1px] border-[var(--border-main)] dark:border-[var(--border-light)] rounded-xl shadow-[0px_8px_32px_0px_rgba(0,0,0,0.16),0px_0px_0px_1px_rgba(0,0,0,0.06)] opacity-0 pointer-events-none -translate-x-10'"
      :style="(isLeftPanelShow ? 'width: 300px;' : 'width: 0px;') + ' transition: opacity 0.2s, transform 0.2s, width 0.2s;'">

      <!-- 顶部折叠按钮 -->
      <div class="flex items-center px-3 h-[52px] flex-shrink-0">
        <div class="flex justify-between w-full px-1 pt-2">
          <div class="relative flex">
            <div
              class="flex h-7 w-7 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md"
              @click="toggleLeftPanel">
              <PanelLeft class="h-5 w-5 text-[var(--icon-secondary)]" />
            </div>
          </div>
        </div>
      </div>

      <!-- 快捷入口区域 -->
      <div class="flex flex-col flex-1 min-h-0 px-[8px] pb-0 gap-px">

        <!-- 新建任务 -->
        <div
          @click="handleNewTaskClick"
          class="flex items-center rounded-[10px] cursor-pointer transition-colors w-full gap-[12px] h-[36px] ps-[9px] pe-[2px]"
          :class="route.path === '/' ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]'">
          <div class="shrink-0 size-[18px] flex items-center justify-center">
            <SquarePen :size="18" class="text-[var(--text-primary)]" />
          </div>
          <div class="flex-1 min-w-0 flex gap-[4px] items-center text-[14px] text-[var(--text-primary)]">
            <span class="truncate">{{ t('New Task') }}</span>
          </div>
          <div class="shrink-0 flex items-center gap-1 pe-[6px]">
            <span class="flex text-[var(--text-tertiary)] justify-center items-center h-5 px-1 rounded-[4px] bg-[var(--fill-tsp-white-light)] border border-[var(--border-light)]">
              <Command :size="12" />
            </span>
            <span class="flex justify-center items-center w-5 h-5 px-1 rounded-[4px] bg-[var(--fill-tsp-white-light)] border border-[var(--border-light)] text-xs text-[var(--text-tertiary)]">
              K
            </span>
          </div>
        </div>

        <!-- 所有任务分组标题 + 会话列表 -->
        <div class="flex flex-col flex-1 min-h-0 -mx-[8px] mt-[4px] overflow-hidden">
          <div class="w-full border-t border-[var(--border-main)] transition-opacity duration-200" :class="isListScrolled ? 'opacity-100' : 'opacity-0'"></div>

          <!-- 滚动容器：标题 + 列表一起滚动 -->
          <div ref="scrollContainerRef" class="flex flex-col flex-1 min-h-0 overflow-y-auto overflow-x-hidden pb-5 px-[8px]" @scroll="handleListScroll">

            <!-- 分组标题 -->
            <div
              class="group flex items-center justify-between ps-[10px] pe-[2px] py-[2px] h-[36px] gap-[12px] flex-shrink-0 cursor-pointer hover:bg-[var(--fill-tsp-white-light)] transition-colors rounded-[10px]"
              @click="isAllTasksCollapsed = !isAllTasksCollapsed">
              <div class="flex items-center flex-1 min-w-0 gap-0.5">
                <span class="text-[13px] leading-[18px] text-[var(--text-tertiary)] font-medium min-w-0 truncate tracking-[-0.091px]">
                  {{ t('All Tasks') }}
                </span>
                <ChevronUp
                  :size="14"
                  class="shrink-0 transition-all opacity-0 group-hover:opacity-100"
                  :class="isAllTasksCollapsed ? 'rotate-180' : 'rotate-90'"
                  stroke="var(--icon-tertiary)" />
              </div>
            </div>

            <!-- 会话列表 -->
            <template v-if="!isAllTasksCollapsed">
              <div v-if="sessions.length > 0" class="flex flex-col gap-px">
                <SessionItem
                  v-for="session in sessions"
                  :key="session.session_id"
                  :session="session"
                  @deleted="handleSessionDeleted" />
              </div>
              <div v-else class="flex flex-col items-center justify-center gap-4 py-8">
                <div class="flex flex-col items-center gap-2 text-[var(--text-tertiary)]">
                  <MessageSquareDashed :size="38" />
                  <span class="text-sm font-medium">{{ t('Create a task to get started') }}</span>
                </div>
              </div>
            </template>

          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PanelLeft, SquarePen, Command, MessageSquareDashed, ChevronUp } from 'lucide-vue-next';
import SessionItem from './SessionItem.vue';
import { useLeftPanel } from '../composables/useLeftPanel';
import { ref, onMounted, watch, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getSessionsSSE, getSessions } from '../api/agent';
import { ListSessionItem } from '../types/response';
import { useI18n } from 'vue-i18n';

const { t } = useI18n()
const { isLeftPanelShow, toggleLeftPanel } = useLeftPanel()
const route = useRoute()
const router = useRouter()

const sessions = ref<ListSessionItem[]>([])
const cancelGetSessionsSSE = ref<(() => void) | null>(null)
const isAllTasksCollapsed = ref(false)
const isListScrolled = ref(false)
const scrollContainerRef = ref<HTMLElement | null>(null)

const handleListScroll = () => {
  if (scrollContainerRef.value) {
    isListScrolled.value = scrollContainerRef.value.scrollTop > 0
  }
}

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
      onOpen: () => {
        console.log('Sessions SSE opened')
      },
      onMessage: (event) => {
        sessions.value = event.data.sessions
      },
      onError: (error) => {
        console.error('Failed to fetch sessions:', error)
      },
      onClose: () => {
        console.log('Sessions SSE closed')
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
