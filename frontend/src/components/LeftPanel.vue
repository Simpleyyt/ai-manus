<template>
  <div class="h-full flex flex-col flex-shrink-0"
    :style="'width: ' + (isLeftPanelShow ? 300 : 52) + 'px; transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);'">
    <div class="flex flex-col overflow-hidden bg-[var(--background-nav)] h-full w-full">

      <!-- 顶部 Logo + 折叠/展开 -->
      <div class="flex items-center justify-between pointer-events-auto h-[56px] px-[8px] py-[12px] flex-shrink-0">
        <div class="flex gap-0.5 items-center">
          <template v-if="isLeftPanelShow">
            <div class="flex items-center justify-center flex-shrink-0 size-[32px] mx-[2px]">
              <Bot :size="28" class="text-[var(--icon-primary)]" />
            </div>
            <ManusLogoTextIcon :width="64.8" :height="28" />
          </template>
          <template v-else>
            <div
              class="group flex items-center justify-center flex-shrink-0 size-[32px] mx-[2px] cursor-pointer rounded-md hover:bg-[var(--fill-tsp-gray-main)]"
              :title="t('Expand sidebar')"
              @click="toggleLeftPanel">
              <Bot :size="28" class="text-[var(--icon-primary)] group-hover:hidden" />
              <PanelLeft class="h-5 w-5 text-[var(--icon-secondary)] hidden group-hover:block" />
            </div>
          </template>
        </div>
        <div v-if="isLeftPanelShow"
          class="flex h-7 w-7 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md"
          :title="t('Collapse sidebar')"
          @click="toggleLeftPanel">
          <PanelLeft class="h-5 w-5 text-[var(--icon-secondary)]" />
        </div>
      </div>

      <!-- 快捷入口 -->
      <div class="flex flex-col flex-1 min-h-0 p-[8px] pb-0 gap-px overflow-hidden">

        <!-- New Task -->
        <div
          @click="handleNewTaskClick"
          :title="isLeftPanelShow ? undefined : t('New Task')"
          class="flex items-center rounded-[10px] clickable cursor-pointer transition-colors w-full gap-[8px] h-[36px] pointer-events-auto p-[9px]"
          :class="route.path === '/' && !isSearchMode ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]'">
          <div class="shrink-0 size-[20px] flex items-center justify-center ltr:-translate-x-px rtl:translate-x-px">
            <SquarePen :size="18" class="text-[var(--text-primary)]" />
          </div>
          <template v-if="isLeftPanelShow">
            <div class="flex-1 min-w-0 flex gap-[4px] items-center text-[14px] text-[var(--text-primary)]">
              <span class="truncate">{{ t('New Task') }}</span>
            </div>
            <div class="shrink-0 flex items-center gap-1">
              <span class="flex text-[var(--text-tertiary)] justify-center items-center h-5 px-1 rounded-[4px] bg-[var(--fill-tsp-white-light)] border border-[var(--border-light)]">
                <Command :size="12" />
              </span>
              <span class="flex justify-center items-center w-5 h-5 px-1 rounded-[4px] bg-[var(--fill-tsp-white-light)] border border-[var(--border-light)] text-xs text-[var(--text-tertiary)]">
                K
              </span>
            </div>
          </template>
        </div>

        <!-- Search -->
        <div
          @click="handleSearchClick"
          :title="isLeftPanelShow ? undefined : t('Search')"
          class="flex items-center rounded-[10px] clickable cursor-pointer transition-colors w-full gap-[8px] h-[36px] pointer-events-auto p-[9px]"
          :class="isSearchMode ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]'">
          <div class="shrink-0 size-[20px] flex items-center justify-center ltr:-translate-x-px rtl:translate-x-px">
            <Search :size="18" class="text-[var(--text-primary)]" />
          </div>
          <div v-if="isLeftPanelShow" class="flex-1 min-w-0 flex gap-[4px] items-center text-[14px] text-[var(--text-primary)]">
            <span class="truncate">{{ t('Search') }}</span>
          </div>
        </div>

        <!-- Library（占位，对齐官方导航） -->
        <div
          @click="handleLibraryClick"
          :title="isLeftPanelShow ? undefined : t('Library')"
          class="flex items-center rounded-[10px] clickable cursor-pointer transition-colors w-full gap-[8px] h-[36px] pointer-events-auto p-[9px] hover:bg-[var(--fill-tsp-white-light)]">
          <div class="shrink-0 size-[20px] flex items-center justify-center ltr:-translate-x-px rtl:translate-x-px">
            <Library :size="18" class="text-[var(--text-primary)]" />
          </div>
          <div v-if="isLeftPanelShow" class="flex-1 min-w-0 flex gap-[4px] items-center text-[14px] text-[var(--text-primary)]">
            <span class="truncate">{{ t('Library') }}</span>
          </div>
        </div>

        <!-- Claw -->
        <div
          v-if="clawEnabled"
          @click="handleClawClick"
          :title="isLeftPanelShow ? undefined : 'Manus Claw'"
          class="flex items-center rounded-[10px] clickable cursor-pointer transition-colors w-full gap-[8px] h-[36px] pointer-events-auto p-[9px]"
          :class="route.path === '/chat/claw' ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]'">
          <div class="shrink-0 size-[20px] flex items-center justify-center ltr:-translate-x-px rtl:translate-x-px">
            <div class="claw-nav-icon w-[18px] h-[18px]" />
          </div>
          <div v-if="isLeftPanelShow" class="flex-1 min-w-0 flex gap-[4px] items-center text-[14px] text-[var(--text-primary)]">
            <span class="truncate">Manus Claw</span>
          </div>
        </div>

        <!-- 任务列表区 -->
        <div v-if="isLeftPanelShow" class="flex flex-col flex-1 min-h-0 -mx-[8px] mt-[4px] overflow-hidden">
          <div class="w-full border-t border-[var(--border-main)] transition-opacity duration-200" :class="isListScrolled ? 'opacity-100' : 'opacity-0'"></div>

          <div ref="scrollContainerRef" class="flex flex-col flex-1 min-h-0 overflow-y-auto overflow-x-hidden pb-5 px-[8px]" @scroll="handleListScroll">

            <!-- Search 输入 -->
            <div v-if="isSearchMode" class="mt-[4px] mb-[8px] px-[2px]">
              <input
                ref="searchInputRef"
                v-model="searchQuery"
                type="text"
                class="w-full h-[36px] px-3 rounded-[10px] border border-[var(--border-main)] bg-[var(--fill-tsp-white-main)] text-[14px] text-[var(--text-primary)] outline-none focus:border-[var(--border-dark)]"
                :placeholder="t('Search for task')"
                @keydown.escape="exitSearchMode"
              />
            </div>

            <!-- Projects 分区 -->
            <template v-if="!isSearchMode">
              <div class="group flex items-center justify-between ps-[10px] pe-[2px] py-[2px] h-[36px] gap-[12px] flex-shrink-0">
                <span class="text-[13px] leading-[18px] text-[var(--text-tertiary)] font-medium min-w-0 truncate tracking-[-0.091px]">
                  {{ t('Projects') }}
                </span>
                <button
                  type="button"
                  class="flex size-7 items-center justify-center rounded-md hover:bg-[var(--fill-tsp-white-light)] text-[var(--icon-tertiary)]"
                  :title="t('New project')"
                  @click.stop="handleNewProjectClick">
                  <Plus :size="16" />
                </button>
              </div>

              <div
                v-if="projects.length === 0"
                class="flex items-center rounded-[10px] clickable cursor-pointer transition-colors w-full gap-[8px] h-[36px] pointer-events-auto p-[9px] hover:bg-[var(--fill-tsp-white-light)]"
                @click="handleNewProjectClick">
                <div class="shrink-0 size-[20px] flex items-center justify-center">
                  <FolderPlus :size="18" class="text-[var(--icon-tertiary)]" />
                </div>
                <span class="text-[14px] text-[var(--text-tertiary)] truncate">{{ t('New project') }}</span>
              </div>

              <template v-for="project in projects" :key="project.project_id">
                <div
                  class="group flex items-center rounded-[10px] clickable cursor-pointer transition-colors w-full gap-[8px] h-[36px] pointer-events-auto ps-[9px] pe-[2px] hover:bg-[var(--fill-tsp-white-light)]"
                  @click="toggleProjectExpand(project.project_id)">
                  <div class="shrink-0 size-[20px] flex items-center justify-center">
                    <Folder :size="18" class="text-[var(--icon-tertiary)]" />
                  </div>
                  <span class="flex-1 min-w-0 truncate text-[14px] text-[var(--text-primary)]">{{ project.name }}</span>
                  <Pin
                    v-if="project.is_pinned"
                    :size="12"
                    class="shrink-0 text-[var(--icon-tertiary)]"
                    fill="var(--icon-tertiary)" />
                  <button
                    type="button"
                    class="hidden group-hover:flex size-7 items-center justify-center rounded-md hover:bg-[var(--fill-tsp-white-main)] text-[var(--icon-tertiary)]"
                    :title="project.is_pinned ? t('Unpin') : t('Pin')"
                    @click.stop="handlePinProject(project)">
                    <Pin :size="14" />
                  </button>
                </div>
                <div v-if="expandedProjectIds.has(project.project_id)" class="ps-[12px] flex flex-col gap-px">
                  <SessionItem
                    v-for="session in sessionsForProject(project.project_id)"
                    :key="session.session_id"
                    :session="session"
                    :projects="projects"
                    @deleted="handleSessionDeleted"
                    @renamed="handleSessionRenamed"
                    @shared="handleSessionShared"
                    @favorited="handleSessionFavorited"
                    @moved="handleSessionMoved" />
                  <div
                    v-if="sessionsForProject(project.project_id).length === 0"
                    class="px-[9px] py-2 text-[12px] text-[var(--text-tertiary)]">
                    {{ t('No tasks in project') }}
                  </div>
                </div>
              </template>
            </template>

            <!-- All tasks + 筛选 -->
            <div ref="filterMenuRef" class="relative mt-[4px]">
              <div
                class="group flex items-center justify-between ps-[10px] pe-[2px] py-[2px] h-[36px] gap-[12px] flex-shrink-0 cursor-pointer hover:bg-[var(--fill-tsp-white-light)] transition-colors rounded-[10px]"
                @click="toggleFilterMenu">
                <div class="flex items-center flex-1 min-w-0 gap-0.5">
                  <span class="text-[13px] leading-[18px] text-[var(--text-tertiary)] font-medium min-w-0 truncate tracking-[-0.091px]">
                    {{ taskFilterLabel }}
                  </span>
                  <ChevronDown
                    :size="14"
                    class="shrink-0 transition-transform"
                    :class="showFilterMenu ? 'rotate-180' : ''"
                    stroke="var(--icon-tertiary)" />
                </div>
              </div>

              <div
                v-if="showFilterMenu"
                class="absolute start-0 top-[36px] z-20 w-[200px] rounded-[12px] border border-[var(--border-dark)] bg-[var(--background-menu-white)] p-1 shadow-lg">
                <button
                  v-for="option in filterOptions"
                  :key="option.key"
                  type="button"
                  class="flex w-full items-center gap-2 rounded-[8px] px-2 h-[36px] text-[14px] text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
                  @click.stop="selectFilter(option.key)">
                  <Check :size="16" class="shrink-0" :class="taskFilter === option.key ? 'opacity-100' : 'opacity-0'" />
                  <span class="truncate">{{ option.label }}</span>
                </button>
              </div>
            </div>

            <!-- 会话列表 -->
            <div v-if="filteredSessions.length > 0" class="flex flex-col gap-px">
              <SessionItem
                v-for="session in filteredSessions"
                :key="session.session_id"
                :session="session"
                :projects="projects"
                @deleted="handleSessionDeleted"
                @renamed="handleSessionRenamed"
                @shared="handleSessionShared"
                @favorited="handleSessionFavorited"
                @moved="handleSessionMoved" />
            </div>
            <div v-else class="flex flex-col items-center justify-center gap-4 py-8">
              <div class="flex flex-col items-center gap-2 text-[var(--text-tertiary)]">
                <MessageSquareDashed :size="38" />
                <span class="text-sm font-medium">{{ emptyListText }}</span>
              </div>
            </div>

          </div>
        </div>
        <template v-else>
          <div class="mx-auto my-[10px] w-[28px] h-[1px] bg-[var(--border-main)]"></div>
          <div class="flex-1"></div>
        </template>

      </div>

      <!-- 底部 Profile -->
      <div ref="profileRef" class="relative flex flex-col justify-center items-start gap-[8px] bg-[var(--background-nav)] p-[8px] flex-shrink-0">
        <div v-if="showUserMenu" class="fixed z-50"
          :class="isLeftPanelShow ? 'start-2 bottom-[52px]' : 'start-[56px] bottom-3'">
          <UserMenu />
        </div>
        <div class="flex w-full items-center justify-between pe-[2px]" :class="isLeftPanelShow ? '' : 'flex-col-reverse gap-[4px]'">
          <div class="flex-1 min-w-0 flex items-center">
            <div
              @click="showUserMenu = !showUserMenu"
              :title="isLeftPanelShow ? undefined : (currentUser?.fullname || t('Unknown User'))"
              class="flex min-w-0 ps-[2px] items-center gap-[8px] clickable cursor-pointer hover:opacity-70 p-[2px] text-[var(--text-primary)] text-sm font-[500]"
              aria-expanded="false" aria-haspopup="dialog">
              <div class="relative flex items-center justify-center font-bold cursor-pointer flex-shrink-0">
                <div
                  class="relative flex items-center justify-center font-bold flex-shrink-0 rounded-full overflow-hidden"
                  style="width: 28px; height: 28px; font-size: 14px; color: rgba(255, 255, 255, 0.9); background-color: rgb(59, 130, 246);">
                  {{ avatarLetter }}
                </div>
              </div>
              <span v-if="isLeftPanelShow" class="truncate">
                {{ currentUser?.fullname || t('Unknown User') }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <LibraryDialog :visible="showLibrary" @close="showLibrary = false" />
</template>

<script setup lang="ts">
import { Bot, PanelLeft, SquarePen, Command, MessageSquareDashed, ChevronDown, Search, Library, Plus, FolderPlus, Check, Pin, Folder } from 'lucide-vue-next';
import SessionItem from './SessionItem.vue';
import UserMenu from './UserMenu.vue';
import LibraryDialog from './LibraryDialog.vue';
import ManusLogoTextIcon from './icons/ManusLogoTextIcon.vue';
import { useLeftPanel } from '../composables/useLeftPanel';
import { useAuth } from '../composables/useAuth';
import { useDialog } from '../composables/useDialog';
import { ref, computed, onMounted, watch, onUnmounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getSessionsSSE, getSessions } from '../api/agent';
import { getProjects, createProject, pinProject } from '../api/project';
import { getCachedClientConfig } from '../api/config';
import { ListSessionItem, ProjectItem } from '../types/response';
import { useI18n } from 'vue-i18n';
import { showSuccessToast, showErrorToast } from '../utils/toast';

type TaskFilter = 'all' | 'favorites' | 'shared' | 'noProject'

const { t } = useI18n()
const { isLeftPanelShow, toggleLeftPanel } = useLeftPanel()
const { showInputDialog } = useDialog()
const route = useRoute()
const router = useRouter()

const sessions = ref<ListSessionItem[]>([])
const projects = ref<ProjectItem[]>([])
const cancelGetSessionsSSE = ref<(() => void) | null>(null)
const isListScrolled = ref(false)
const clawEnabled = ref(false)
const scrollContainerRef = ref<HTMLElement | null>(null)
const searchInputRef = ref<HTMLInputElement | null>(null)
const filterMenuRef = ref<HTMLElement | null>(null)

const isSearchMode = ref(false)
const searchQuery = ref('')
const taskFilter = ref<TaskFilter>('all')
const showFilterMenu = ref(false)
const showLibrary = ref(false)
const expandedProjectIds = ref<Set<string>>(new Set())

const { currentUser } = useAuth()
const showUserMenu = ref(false)
const profileRef = ref<HTMLElement | null>(null)

const avatarLetter = computed(() => {
  return currentUser.value?.fullname?.charAt(0)?.toUpperCase() || 'M'
})

const filterOptions = computed(() => [
  { key: 'all' as const, label: t('All Tasks') },
  { key: 'noProject' as const, label: t('Non-project tasks') },
  { key: 'favorites' as const, label: t('Favorites') },
  { key: 'shared' as const, label: t('Shared') },
])

const taskFilterLabel = computed(() => {
  return filterOptions.value.find(o => o.key === taskFilter.value)?.label || t('All Tasks')
})

const filteredSessions = computed(() => {
  let list = sessions.value

  if (taskFilter.value === 'favorites') {
    list = list.filter(s => s.is_favorite)
  } else if (taskFilter.value === 'shared') {
    list = list.filter(s => s.is_shared)
  } else if (taskFilter.value === 'noProject') {
    list = list.filter(s => !s.project_id)
  }

  const q = searchQuery.value.trim().toLowerCase()
  if (isSearchMode.value && q) {
    list = list.filter(s => (s.title || '').toLowerCase().includes(q))
  }

  // When showing all tasks without search, hide sessions already nested under expanded projects
  // Keep them in list for "all" - Manus shows all tasks separately from projects. Keep flat list for all/noProject/favorites/shared.
  return list
})

const emptyListText = computed(() => {
  if (isSearchMode.value && searchQuery.value.trim()) {
    return t('No matching tasks')
  }
  if (taskFilter.value === 'favorites') {
    return t('No favorite tasks')
  }
  if (taskFilter.value === 'shared') {
    return t('No shared tasks')
  }
  if (taskFilter.value === 'noProject') {
    return t('No non-project tasks')
  }
  return t('Create a task to get started')
})

const sessionsForProject = (projectId: string) => {
  return sessions.value.filter(s => s.project_id === projectId)
}

const handleClickOutside = (event: MouseEvent) => {
  if (showUserMenu.value && profileRef.value && !profileRef.value.contains(event.target as Node)) {
    showUserMenu.value = false
  }
  if (showFilterMenu.value && filterMenuRef.value && !filterMenuRef.value.contains(event.target as Node)) {
    showFilterMenu.value = false
  }
}

const handleListScroll = () => {
  if (scrollContainerRef.value) {
    isListScrolled.value = scrollContainerRef.value.scrollTop > 0
  }
}

const updateSessions = async () => {
  try {
    const response = await getSessions()
    sessions.value = response.sessions
  } catch (error) {
    console.error('Failed to fetch sessions:', error)
  }
}

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
  isSearchMode.value = false
  searchQuery.value = ''
  router.push('/')
}

const handleSearchClick = async () => {
  if (!isLeftPanelShow.value) {
    toggleLeftPanel()
  }
  isSearchMode.value = true
  await nextTick()
  searchInputRef.value?.focus()
}

const exitSearchMode = () => {
  isSearchMode.value = false
  searchQuery.value = ''
}

const handleLibraryClick = () => {
  showLibrary.value = true
}

const handleNewProjectClick = () => {
  showInputDialog({
    title: t('New project'),
    placeholder: t('Enter project name'),
    confirmText: t('Create'),
    onConfirm: async (value: string) => {
      if (!value) return
      try {
        const project = await createProject(value)
        projects.value = [project, ...projects.value]
        expandedProjectIds.value = new Set([...expandedProjectIds.value, project.project_id])
        showSuccessToast(t('Project created'))
      } catch {
        showErrorToast(t('Failed to create project'))
      }
    }
  })
}

const toggleProjectExpand = (projectId: string) => {
  const next = new Set(expandedProjectIds.value)
  if (next.has(projectId)) next.delete(projectId)
  else next.add(projectId)
  expandedProjectIds.value = next
}

const handlePinProject = async (project: ProjectItem) => {
  try {
    const updated = await pinProject(project.project_id, !project.is_pinned)
    projects.value = projects.value
      .map(p => p.project_id === updated.project_id ? updated : p)
      .sort((a, b) => Number(b.is_pinned) - Number(a.is_pinned))
    showSuccessToast(updated.is_pinned ? t('Pinned') : t('Unpinned'))
  } catch {
    showErrorToast(t('Failed to update project'))
  }
}

const loadProjects = async () => {
  try {
    const res = await getProjects()
    projects.value = res.projects
  } catch (e) {
    console.error('Failed to load projects', e)
  }
}

const handleClawClick = () => {
  router.push('/chat/claw')
}

const toggleFilterMenu = () => {
  showFilterMenu.value = !showFilterMenu.value
}

const selectFilter = (key: TaskFilter) => {
  taskFilter.value = key
  showFilterMenu.value = false
}

const handleSessionDeleted = (sessionId: string) => {
  sessions.value = sessions.value.filter(session => session.session_id !== sessionId)
}

const handleSessionRenamed = (sessionId: string, title: string) => {
  sessions.value = sessions.value.map(session =>
    session.session_id === sessionId ? { ...session, title } : session
  )
}

const handleSessionShared = (sessionId: string) => {
  sessions.value = sessions.value.map(session =>
    session.session_id === sessionId ? { ...session, is_shared: true } : session
  )
}

const handleSessionFavorited = (sessionId: string, isFavorite: boolean) => {
  sessions.value = sessions.value.map(session =>
    session.session_id === sessionId ? { ...session, is_favorite: isFavorite } : session
  )
}

const handleSessionMoved = (sessionId: string, projectId: string | null) => {
  sessions.value = sessions.value.map(session =>
    session.session_id === sessionId ? { ...session, project_id: projectId } : session
  )
  if (projectId) {
    expandedProjectIds.value = new Set([...expandedProjectIds.value, projectId])
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
    event.preventDefault()
    handleNewTaskClick()
  }
}

onMounted(async () => {
  getCachedClientConfig().then(cfg => {
    clawEnabled.value = cfg?.claw_enabled ?? false
  })

  fetchSessions()
  loadProjects()

  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  if (cancelGetSessionsSSE.value) {
    cancelGetSessionsSSE.value()
    cancelGetSessionsSSE.value = null
  }

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
