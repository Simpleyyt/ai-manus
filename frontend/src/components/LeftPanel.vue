<template>
  <div class="h-full flex flex-col flex-shrink-0"
    :style="'width: ' + (isLeftPanelShow ? 300 : 60) + 'px; transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);'">
    <div class="flex flex-col overflow-hidden bg-[var(--background-nav)] h-full w-full">

      <!-- 顶部 Logo + 折叠/展开按钮(结构复刻自 manus.im 侧边栏顶部) -->
      <div class="flex items-center flex-shrink-0 h-[52px]"
        :class="isLeftPanelShow ? 'justify-between px-4 pt-2' : 'justify-center pt-2'">
        <template v-if="isLeftPanelShow">
          <div class="flex gap-0.5 w-fit items-center">
            <ManusLogoIcon :width="21.4" :height="28" />
            <ManusLogoTextIcon :width="64.8" :height="28" />
          </div>
          <div
            class="flex h-7 w-7 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md"
            :title="t('Collapse sidebar')"
            @click="toggleLeftPanel">
            <PanelLeft class="h-5 w-5 text-[var(--icon-secondary)]" />
          </div>
        </template>
        <template v-else>
          <!-- 收起状态：默认显示 logo，悬停变为展开按钮 -->
          <div
            class="group flex h-9 w-9 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md"
            :title="t('Expand sidebar')"
            @click="toggleLeftPanel">
            <ManusLogoIcon :width="21.4" :height="28" class="group-hover:hidden" />
            <PanelLeft class="h-5 w-5 text-[var(--icon-secondary)] hidden group-hover:block" />
          </div>
        </template>
      </div>

      <!-- 快捷入口区域 -->
      <div class="flex flex-col flex-1 min-h-0 pb-0 gap-px" :class="isLeftPanelShow ? 'px-[8px]' : 'px-[12px] items-center'">

        <!-- 新建任务 -->
        <div
          @click="handleNewTaskClick"
          :title="isLeftPanelShow ? undefined : t('New Task')"
          class="flex items-center rounded-[10px] cursor-pointer transition-colors h-[36px]"
          :class="[
            isLeftPanelShow ? 'w-full gap-[12px] ps-[9px] pe-[2px]' : 'w-9 justify-center',
            route.path === '/' ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]'
          ]">
          <div class="shrink-0 size-[18px] flex items-center justify-center">
            <SquarePen :size="18" class="text-[var(--text-primary)]" />
          </div>
          <template v-if="isLeftPanelShow">
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
          </template>
        </div>

        <!-- Claw 入口 -->
        <div
          v-if="clawEnabled"
          @click="handleClawClick"
          :title="isLeftPanelShow ? undefined : 'Manus Claw'"
          class="flex items-center rounded-[10px] cursor-pointer transition-colors h-[36px]"
          :class="[
            isLeftPanelShow ? 'w-full gap-[12px] ps-[9px] pe-[2px]' : 'w-9 justify-center',
            route.path === '/chat/claw' ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]'
          ]">
          <div class="shrink-0 size-[18px] flex items-center justify-center">
            <div class="claw-nav-icon w-[18px] h-[18px]" />
          </div>
          <div v-if="isLeftPanelShow" class="flex-1 min-w-0 flex gap-[4px] items-center text-[14px] text-[var(--text-primary)]">
            <span class="truncate">Manus Claw</span>
          </div>
        </div>

        <!-- 所有任务分组标题 + 会话列表(仅展开时显示) -->
        <div v-if="isLeftPanelShow" class="flex flex-col flex-1 min-h-0 -mx-[8px] mt-[4px] overflow-hidden">
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
        <div v-else class="flex-1"></div>

      </div>

      <!-- 底部个人 Profile(结构复刻自 manus.im 侧边栏底部) -->
      <div ref="profileRef" class="relative flex-shrink-0 pb-3 pt-1" :class="isLeftPanelShow ? 'px-[8px]' : 'px-[10px] flex justify-center'">
        <div v-if="showUserMenu" class="absolute z-50"
          :class="isLeftPanelShow ? 'bottom-full start-2 mb-1' : 'bottom-2 start-full ms-1'">
          <UserMenu />
        </div>
        <div
          @click="showUserMenu = !showUserMenu"
          :title="isLeftPanelShow ? undefined : (currentUser?.fullname || t('Unknown User'))"
          class="flex items-center rounded-[10px] cursor-pointer transition-colors"
          :class="[
            isLeftPanelShow ? 'w-full gap-[8px] h-[48px] px-[8px]' : 'w-10 h-10 justify-center',
            showUserMenu ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]'
          ]">
          <div
            class="relative flex items-center justify-center font-bold flex-shrink-0 rounded-full overflow-hidden"
            style="width: 32px; height: 32px; font-size: 16px; color: rgba(255, 255, 255, 0.9); background-color: rgb(59, 130, 246);">
            {{ avatarLetter }}
          </div>
          <div v-if="isLeftPanelShow" class="flex flex-col flex-1 min-w-0">
            <span class="text-[14px] leading-[18px] text-[var(--text-primary)] font-medium truncate">
              {{ currentUser?.fullname || t('Unknown User') }}
            </span>
            <span class="text-[12px] leading-[16px] text-[var(--text-tertiary)] truncate">
              {{ currentUser?.email || t('No email') }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PanelLeft, SquarePen, Command, MessageSquareDashed, ChevronUp } from 'lucide-vue-next';
import SessionItem from './SessionItem.vue';
import UserMenu from './UserMenu.vue';
import ManusLogoIcon from './icons/ManusLogoIcon.vue';
import ManusLogoTextIcon from './icons/ManusLogoTextIcon.vue';
import { useLeftPanel } from '../composables/useLeftPanel';
import { useAuth } from '../composables/useAuth';
import { ref, computed, onMounted, watch, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getSessionsSSE, getSessions } from '../api/agent';
import { getCachedClientConfig } from '../api/config';
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
const clawEnabled = ref(false)
const scrollContainerRef = ref<HTMLElement | null>(null)

// Bottom profile entry
const { currentUser } = useAuth()
const showUserMenu = ref(false)
const profileRef = ref<HTMLElement | null>(null)

const avatarLetter = computed(() => {
  return currentUser.value?.fullname?.charAt(0)?.toUpperCase() || 'M'
})

const handleClickOutside = (event: MouseEvent) => {
  if (showUserMenu.value && profileRef.value && !profileRef.value.contains(event.target as Node)) {
    showUserMenu.value = false
  }
}

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

const handleClawClick = () => {
  router.push('/chat/claw')
}

const handleSessionDeleted = (sessionId: string) => {
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
  getCachedClientConfig().then(cfg => {
    clawEnabled.value = cfg?.claw_enabled ?? false
  })

  // Initial fetch of sessions
  fetchSessions()

  // Add keyboard event listener
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  if (cancelGetSessionsSSE.value) {
    cancelGetSessionsSSE.value()
    cancelGetSessionsSSE.value = null
  }

  // Remove keyboard event listener
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('mousedown', handleClickOutside)
})

watch(() => route.path, async () => {
  await updateSessions()
})
</script>

<style scoped>
.claw-nav-icon {
  background: url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='20'%20height='20'%20fill='none'%20viewBox='0%200%2020%2020'%20opacity='0.84'%3e%3cpath%20fill='%23333'%20fill-opacity='.9'%20fill-rule='evenodd'%20d='M5.724%204.379c3.934-3.078%207.519-2.009%208.808-.972.675.543%201.05%201.332.97%202.126-.082.823-.64%201.509-1.529%201.805-.463.155-.831.552-.998%201.034-.168.485-.1.942.144%201.24l.027.035a1%201%200%200%201%20.077.018c.265.08.413.122.617.076.202-.046.58-.215%201.13-.88l.127-.136a1.44%201.44%200%200%201%201.082-.402c.418.022.797.215%201.075.482.32.31.466.77.526%201.17.065.43.051.928-.057%201.434-.217%201.017-.837%202.142-2.09%202.82-.402.217-1.098.61-2.146.663a5%205%200%200%201-.376.504c-1.007%201.196-2.394%201.608-3.628%201.57a5.1%205.1%200%200%201-1.6-.312%203.4%203.4%200%200%201-.612.59c-.413.298-.985.518-1.667.347-1.319-.33-2.607-1.6-3.249-3.17-.344-.843-.14-1.573.285-2.087.228-.275.509-.48.777-.624a7.4%207.4%200%200%201-.33-2.307c.037-1.671.705-3.512%202.637-5.024m7.867.197c-.748-.602-3.56-1.662-6.942.985-1.551%201.213-2.034%202.618-2.061%203.874a6.1%206.1%200%200%200%20.805%203.094.75.75%200%200%201-1.29.766q-.05-.09-.103-.188a1%201%200%200%200-.203.182.47.47%200%200%200-.11.22.6.6%200%200%200%20.057.343c.515%201.26%201.491%202.1%202.225%202.285.138.035.262.008.425-.11q.096-.07.188-.167a3%203%200%200%201-.137-.145.75.75%200%200%201%201.136-.98c.294.34%201.034.704%201.948.732.877.027%201.782-.262%202.435-1.037.652-.774.809-1.508.746-2.142-.063-.632-.354-1.218-.711-1.672-.13-.103-.398-.251-.777-.376a4.1%204.1%200%200%200-1.234-.213.75.75%200%200%201%200-1.5c.469%200%20.955.077%201.4.198.017-.29.076-.576.169-.844.297-.856.974-1.644%201.942-1.966.378-.127.492-.348.51-.532.022-.213-.074-.53-.418-.807m2.527%205.25c-.675.81-1.314%201.235-1.947%201.378q-.082.017-.16.027c.093.287.16.591.192.91a4%204%200%200%201-.046%201.116c.299-.098.542-.23.763-.349.79-.428%201.19-1.134%201.336-1.812.073-.341.077-.657.04-.898-.033-.222-.087-.31-.09-.319a.3.3%200%200%200-.067-.046q-.013-.006-.021-.007'%20clip-rule='evenodd'%20/%3e%3c%2fsvg%3e") no-repeat center;
  background-size: contain;
}

:global(.dark) .claw-nav-icon {
  background-image: url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='20'%20height='20'%20fill='none'%20viewBox='0%200%2020%2020'%20opacity='0.84'%3e%3cpath%20fill='%23fff'%20fill-opacity='.9'%20fill-rule='evenodd'%20d='M5.724%204.379c3.934-3.078%207.519-2.009%208.808-.972.675.543%201.05%201.332.97%202.126-.082.823-.64%201.509-1.529%201.805-.463.155-.831.552-.998%201.034-.168.485-.1.942.144%201.24l.027.035a1%201%200%200%201%20.077.018c.265.08.413.122.617.076.202-.046.58-.215%201.13-.88l.127-.136a1.44%201.44%200%200%201%201.082-.402c.418.022.797.215%201.075.482.32.31.466.77.526%201.17.065.43.051.928-.057%201.434-.217%201.017-.837%202.142-2.09%202.82-.402.217-1.098.61-2.146.663a5%205%200%200%201-.376.504c-1.007%201.196-2.394%201.608-3.628%201.57a5.1%205.1%200%200%201-1.6-.312%203.4%203.4%200%200%201-.612.59c-.413.298-.985.518-1.667.347-1.319-.33-2.607-1.6-3.249-3.17-.344-.843-.14-1.573.285-2.087.228-.275.509-.48.777-.624a7.4%207.4%200%200%201-.33-2.307c.037-1.671.705-3.512%202.637-5.024m7.867.197c-.748-.602-3.56-1.662-6.942.985-1.551%201.213-2.034%202.618-2.061%203.874a6.1%206.1%200%200%200%20.805%203.094.75.75%200%200%201-1.29.766q-.05-.09-.103-.188a1%201%200%200%200-.203.182.47.47%200%200%200-.11.22.6.6%200%200%200%20.057.343c.515%201.26%201.491%202.1%202.225%202.285.138.035.262.008.425-.11q.096-.07.188-.167a3%203%200%200%201-.137-.145.75.75%200%200%201%201.136-.98c.294.34%201.034.704%201.948.732.877.027%201.782-.262%202.435-1.037.652-.774.809-1.508.746-2.142-.063-.632-.354-1.218-.711-1.672-.13-.103-.398-.251-.777-.376a4.1%204.1%200%200%200-1.234-.213.75.75%200%200%201%200-1.5c.469%200%20.955.077%201.4.198.017-.29.076-.576.169-.844.297-.856.974-1.644%201.942-1.966.378-.127.492-.348.51-.532.022-.213-.074-.53-.418-.807m2.527%205.25c-.675.81-1.314%201.235-1.947%201.378q-.082.017-.16.027c.093.287.16.591.192.91a4%204%200%200%201-.046%201.116c.299-.098.542-.23.763-.349.79-.428%201.19-1.134%201.336-1.812.073-.341.077-.657.04-.898-.033-.222-.087-.31-.09-.319a.3.3%200%200%200-.067-.046q-.013-.006-.021-.007'%20clip-rule='evenodd'%20/%3e%3c%2fsvg%3e");
}
</style>
