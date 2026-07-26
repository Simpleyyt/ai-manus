<template>
  <nav
    class="bg-[var(--background-nav)] flex flex-col transition-[width,transform] duration-200 h-full border-e border-[var(--border-main)] flex-shrink-0"
    :style="'width: ' + (isSessionSidebarShow ? 300 : 52) + 'px'">
    <div class="flex flex-col flex-1 min-h-0">

      <!-- Header — official: h-56 ps-12 pe-10; Search + Collapse on the right -->
      <div
        class="flex items-center justify-between pointer-events-auto h-[56px] py-[12px] flex-shrink-0"
        :class="isSessionSidebarShow ? 'pe-[10px] ps-[12px]' : 'px-[8px]'">
        <div class="flex gap-0.5 items-center min-w-0" :class="isSessionSidebarShow ? 'clickable' : ''">
          <template v-if="isSessionSidebarShow">
            <div class="flex items-center justify-center flex-shrink-0">
              <Bot :size="28" class="text-[var(--icon-primary)]" />
            </div>
            <ManusLogoTextIcon :width="64.8" :height="28" />
          </template>
          <template v-else>
            <div
              class="group flex items-center justify-center flex-shrink-0 size-[32px] mx-[2px] cursor-pointer rounded-md hover:bg-[var(--fill-tsp-gray-main)]"
              :title="t('Expand sidebar')"
              @click="toggleSessionSidebar">
              <Bot :size="28" class="text-[var(--icon-primary)] group-hover:hidden" />
              <PanelLeft class="h-[18px] w-[18px] text-[var(--icon-secondary)] hidden group-hover:block" />
            </div>
          </template>
        </div>
        <template v-if="isSessionSidebarShow">
          <div
            class="flex items-center justify-center cursor-pointer rounded-md hover:bg-[var(--fill-tsp-white-light)] size-[32px] ms-auto me-[4px]"
            :title="t('Search')"
            @click="handleSearchClick">
            <Search class="size-[18px] text-[var(--icon-secondary)]" />
          </div>
          <div
            class="flex items-center justify-center rounded-md hover:bg-[var(--fill-tsp-white-light)] cursor-pointer size-[32px]"
            :title="t('Collapse sidebar')"
            @click="toggleSessionSidebar">
            <PanelLeft class="size-[18px] text-[var(--icon-secondary)]" />
          </div>
        </template>
      </div>

      <!-- Body — official: p-[8px] pb-0 gap-px -->
      <div
        class="flex flex-col flex-1 min-h-0 pb-0 gap-px overflow-hidden"
        :class="isSessionSidebarShow ? 'p-[8px]' : 'p-[8px]'">

        <!-- New Task -->
        <div
          @click="handleNewTaskClick"
          :title="isSessionSidebarShow ? undefined : t('New Task')"
          class="flex items-center rounded-[10px] clickable cursor-pointer transition-colors w-full gap-[8px] h-[36px] pointer-events-auto ps-[8px] pe-[2px] group"
          :class="route.path === '/' ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]'">
          <div class="shrink-0 size-[20px] flex items-center justify-center">
            <SquarePen :size="18" class="text-[var(--text-primary)]" />
          </div>
          <template v-if="isSessionSidebarShow">
            <div class="flex-1 min-w-0 flex gap-[4px] items-center text-[14px] text-[var(--text-primary)]">
              <span class="truncate">{{ t('New Task') }}</span>
            </div>
            <span class="shrink-0 text-[11px] text-[var(--text-tertiary)] ms-auto pe-[6px] opacity-0 group-hover:opacity-100 transition-opacity">
              {{ newTaskShortcut }}
            </span>
          </template>
        </div>

        <!-- Agent / Plugins / Scheduled — product not wired; hidden -->

        <!-- Library — full page /library -->
        <div
          @click="handleLibraryClick"
          :title="isSessionSidebarShow ? undefined : t('Library')"
          class="flex items-center rounded-[10px] clickable cursor-pointer transition-colors w-full gap-[8px] h-[36px] pointer-events-auto ps-[8px] pe-[2px]"
          :class="route.path === '/library' ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]'">
          <div class="shrink-0 size-[20px] flex items-center justify-center">
            <LibraryBig :size="18" class="text-[var(--text-primary)]" />
          </div>
          <div v-if="isSessionSidebarShow" class="flex-1 min-w-0 flex gap-[4px] items-center text-[14px] text-[var(--text-primary)]">
            <span class="truncate">{{ t('Library') }}</span>
          </div>
        </div>

        <!-- Claw (product-specific) -->
        <div
          v-if="clawEnabled"
          @click="handleClawClick"
          :title="isSessionSidebarShow ? undefined : 'Manus Claw'"
          class="flex items-center rounded-[10px] clickable cursor-pointer transition-colors w-full gap-[8px] h-[36px] pointer-events-auto ps-[8px] pe-[2px]"
          :class="route.path === '/chat/claw' ? 'bg-[var(--fill-tsp-white-main)]' : 'hover:bg-[var(--fill-tsp-white-light)]'">
          <div class="shrink-0 size-[20px] flex items-center justify-center">
            <div class="claw-nav-icon w-[18px] h-[18px]" />
          </div>
          <div v-if="isSessionSidebarShow" class="flex-1 min-w-0 flex gap-[4px] items-center text-[14px] text-[var(--text-primary)]">
            <span class="truncate">Manus Claw</span>
          </div>
        </div>

        <!-- Scroll: Projects + Tasks -->
        <div v-if="isSessionSidebarShow" class="flex flex-col flex-1 min-h-0 -mx-[8px] overflow-hidden">
          <div
            class="w-full border-t-[1px] border-[var(--border-light)] transition-opacity duration-200"
            :class="isListScrolled ? 'opacity-100' : 'opacity-0'"></div>

          <div
            ref="scrollContainerRef"
            class="relative flex flex-col flex-1 min-h-0 overflow-y-auto overflow-x-hidden pb-5 px-[8px]"
            @scroll="handleListScroll">

            <!-- Official: Pinned (已固定) — pinned projects leave Projects list -->
            <div
              v-if="pinnedProjects.length > 0"
              class="flex flex-col gap-px bg-[var(--background-nav)]">
              <div
                class="group flex items-center justify-between ps-[10px] pe-[2px] py-[2px] h-[36px] gap-[12px] clickable sticky top-0 z-[3] bg-[var(--background-nav)] cursor-pointer"
                @click="pinnedCollapsed = !pinnedCollapsed">
                <div class="absolute inset-0 rounded-[10px] opacity-0 group-hover:opacity-100 group-hover:bg-[var(--fill-tsp-white-light)] group-active:opacity-100 bg-[var(--fill-tsp-white-dark)] transition-opacity pointer-events-none" />
                <div class="flex items-center flex-1 min-w-0 gap-0.5">
                  <span class="text-[13px] leading-[18px] text-[var(--text-tertiary)] font-medium min-w-0 truncate tracking-[-0.091px]">
                    {{ t('Pinned') }}
                  </span>
                  <ChevronUp
                    :size="14"
                    class="transition-transform shrink-0 opacity-0 group-hover:opacity-100"
                    :class="pinnedCollapsed ? '' : 'rotate-180'"
                    stroke="var(--icon-tertiary)" />
                </div>
                <div class="flex items-center justify-center">
                  <div />
                </div>
              </div>

              <div v-if="!pinnedCollapsed" class="flex flex-col w-full gap-px">
                <div
                  v-for="project in pinnedProjects"
                  :key="`pinned-${project.project_id}`"
                  class="flex flex-col gap-px">
                  <div
                    class="nav-bar-project-item-header w-full flex items-center overflow-hidden h-[36px] ps-[8px] pe-[2px] gap-[12px] sticky top-[36px] z-[1] bg-[var(--background-nav)] clickable group cursor-pointer"
                    :class="isActiveProject(project.project_id)
                      ? 'rounded-[10px] shadow-[inset_0_0_0_100px_var(--fill-tsp-white-main)]'
                      : 'hover:rounded-[10px] hover:shadow-[inset_0_0_0_100px_var(--fill-tsp-white-light)]'"
                    @click="openProject(project.project_id)">
                    <div class="flex flex-1 items-center gap-[8px] min-w-0">
                      <div class="flex items-center justify-center relative size-[20px] flex-shrink-0 group/icon">
                        <div
                          class="absolute inset-0 flex items-center justify-center group-hover:invisible"
                          :class="expandedProjectIds.has(project.project_id) ? 'invisible' : 'visible'">
                          <Folder :size="18" class="text-[var(--icon-primary)]" stroke="var(--icon-primary)" />
                        </div>
                        <div
                          class="absolute inset-0 flex items-center justify-center rounded-[8px] hover:bg-[var(--fill-tsp-white-light)] clickable invisible group-hover:visible"
                          :class="expandedProjectIds.has(project.project_id) ? '!visible' : ''"
                          :title="expandedProjectIds.has(project.project_id) ? t('Collapse') : t('Expand')"
                          @click.stop="toggleProjectExpand(project.project_id)">
                          <ChevronRight
                            :size="18"
                            class="text-[var(--icon-tertiary)] transition-transform duration-200"
                            :class="expandedProjectIds.has(project.project_id) ? 'rotate-90' : 'rotate-0'"
                          />
                        </div>
                      </div>
                      <span
                        class="text-[var(--text-primary)] text-sm truncate"
                        :title="project.name">
                        {{ project.name || t('Untitled') }}
                      </span>
                    </div>
                    <div class="flex items-center flex-shrink-0 opacity-0 group-hover:opacity-100">
                      <!-- Official: … menu (pin/edit/view/delete) + SquarePen shortcut -->
                      <button
                        type="button"
                        class="size-[32px] flex rounded-[8px] items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-white-light)] text-[var(--icon-tertiary)]"
                        :title="t('More options')"
                        @click.stop="handleProjectMenuClick($event, project)">
                        <Ellipsis :size="18" />
                      </button>
                      <button
                        type="button"
                        class="size-[32px] flex rounded-[8px] items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-white-light)] text-[var(--icon-tertiary)]"
                        :title="t('Edit')"
                        @click.stop="handleEditProject(project)">
                        <SquarePen :size="16" />
                      </button>
                    </div>
                  </div>
                  <div
                    v-if="expandedProjectIds.has(project.project_id)"
                    class="flex flex-col gap-[4px] overflow-hidden w-full">
                    <SessionItem
                      v-for="session in sessionsForProject(project.project_id)"
                      :key="session.session_id"
                      :session="session"
                      :projects="projects"
                      row-class="!ps-[24px]"
                      @deleted="handleSessionDeleted"
                      @renamed="handleSessionRenamed"
                      @shared="handleSessionShared"
                      @favorited="handleSessionFavorited"
                      @pinned="handleSessionPinned"
                      @moved="handleSessionMoved" />
                    <div
                      v-if="sessionsForProject(project.project_id).length === 0"
                      class="flex items-center ps-[36px] pe-[8px] h-[36px]">
                      <span class="text-[var(--text-disable)] text-sm">{{ t('No tasks yet') }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Projects — official unpinnedProjects only -->
              <div
                class="group flex items-center justify-between ps-[10px] pe-[2px] py-[2px] h-[36px] gap-[12px] clickable sticky top-0 z-[3] bg-[var(--background-nav)] cursor-pointer"
                @click="projectsCollapsed = !projectsCollapsed">
                <div class="absolute inset-0 rounded-[10px] opacity-0 group-hover:opacity-100 group-hover:bg-[var(--fill-tsp-white-light)] transition-opacity pointer-events-none"></div>
                <div class="flex items-center flex-1 min-w-0 gap-0.5 relative">
                  <span class="text-[13px] leading-[18px] text-[var(--text-tertiary)] font-medium min-w-0 truncate tracking-[-0.091px]">
                    {{ t('Projects') }}
                  </span>
                  <ChevronUp
                    :size="14"
                    class="transition-transform shrink-0 opacity-0 group-hover:opacity-100"
                    :class="projectsCollapsed ? '' : 'rotate-180'"
                    stroke="var(--icon-tertiary)" />
                </div>
                <button
                  type="button"
                  class="relative flex items-center justify-center size-[32px] rounded-[8px] hover:bg-[var(--fill-tsp-white-main)] clickable text-[var(--icon-tertiary)]"
                  :title="t('New project')"
                  @click.stop="handleNewProjectClick">
                  <Plus :size="18" />
                </button>
              </div>

              <div v-if="!projectsCollapsed" class="flex flex-col w-full gap-px">
                <div
                  v-if="unpinnedProjects.length === 0"
                  class="w-full flex items-center rounded-[10px] h-[36px] ps-[8px] pe-[8px] gap-[8px] hover:bg-[var(--fill-tsp-white-light)] clickable cursor-pointer"
                  @click="handleNewProjectClick">
                  <div class="flex size-[20px] shrink-0 items-center justify-center">
                    <FolderPlus :size="18" class="text-[var(--icon-primary)]" />
                  </div>
                  <span class="text-[var(--text-primary)] text-sm">{{ t('New project') }}</span>
                </div>

                <template v-for="project in unpinnedProjects" :key="project.project_id">
                  <!-- Official nav-bar-project-item-header -->
                  <div
                    class="nav-bar-project-item-header w-full flex items-center overflow-hidden h-[36px] ps-[8px] pe-[2px] gap-[12px] clickable group cursor-pointer"
                    :class="isActiveProject(project.project_id)
                      ? 'rounded-[10px] shadow-[inset_0_0_0_100px_var(--fill-tsp-white-main)]'
                      : 'hover:rounded-[10px] hover:shadow-[inset_0_0_0_100px_var(--fill-tsp-white-light)]'"
                    @click="openProject(project.project_id)">
                    <div class="flex flex-1 items-center gap-[8px] min-w-0">
                      <!-- Icon ↔ ChevronRight on hover (official group/icon) -->
                      <div class="flex items-center justify-center relative size-[20px] flex-shrink-0">
                        <div
                          class="absolute inset-0 flex items-center justify-center group-hover:invisible"
                          :class="expandedProjectIds.has(project.project_id) ? 'invisible' : 'visible'">
                          <Folder :size="18" class="text-[var(--icon-tertiary)]" />
                        </div>
                        <div
                          class="absolute inset-0 flex items-center justify-center rounded-[8px] hover:bg-[var(--fill-tsp-white-light)] clickable invisible group-hover:visible"
                          :class="expandedProjectIds.has(project.project_id) ? '!visible' : ''"
                          :title="expandedProjectIds.has(project.project_id) ? t('Collapse') : t('Expand')"
                          @click.stop="toggleProjectExpand(project.project_id)">
                          <ChevronRight
                            :size="18"
                            class="text-[var(--icon-tertiary)] transition-transform duration-200"
                            :class="expandedProjectIds.has(project.project_id) ? 'rotate-90' : 'rotate-0'"
                          />
                        </div>
                      </div>
                      <span
                        class="text-[var(--text-primary)] text-sm truncate"
                        :title="project.name">
                        {{ project.name || t('Untitled') }}
                      </span>
                    </div>
                    <div class="flex items-center flex-shrink-0 opacity-0 group-hover:opacity-100">
                      <!-- Official: … menu (pin/edit/view/delete) + SquarePen shortcut -->
                      <button
                        type="button"
                        class="size-[32px] flex rounded-[8px] items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-white-light)] text-[var(--icon-tertiary)]"
                        :title="t('More options')"
                        @click.stop="handleProjectMenuClick($event, project)">
                        <Ellipsis :size="18" />
                      </button>
                      <button
                        type="button"
                        class="size-[32px] flex rounded-[8px] items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-white-light)] text-[var(--icon-tertiary)]"
                        :title="t('Edit')"
                        @click.stop="handleEditProject(project)">
                        <SquarePen :size="16" />
                      </button>
                    </div>
                  </div>
                  <div
                    v-if="expandedProjectIds.has(project.project_id)"
                    class="flex flex-col gap-[4px] overflow-hidden w-full">
                    <SessionItem
                      v-for="session in sessionsForProject(project.project_id)"
                      :key="session.session_id"
                      :session="session"
                      :projects="projects"
                      row-class="!ps-[24px]"
                      @deleted="handleSessionDeleted"
                      @renamed="handleSessionRenamed"
                      @shared="handleSessionShared"
                      @favorited="handleSessionFavorited"
                      @pinned="handleSessionPinned"
                      @moved="handleSessionMoved" />
                    <div
                      v-if="sessionsForProject(project.project_id).length === 0"
                      class="flex items-center ps-[36px] pe-[8px] h-[36px]">
                      <span class="text-[var(--text-disable)] text-sm">{{ t('No tasks yet') }}</span>
                    </div>
                  </div>
                </template>
              </div>

            <!-- Tasks + filter -->
            <div ref="filterMenuRef" class="relative">
              <div
                class="group flex items-center justify-between ps-[10px] pe-[2px] py-[2px] h-[36px] gap-[12px] clickable sticky top-0 z-[3] bg-[var(--background-nav)] cursor-pointer"
                @click="tasksCollapsed = !tasksCollapsed">
                <div class="absolute inset-0 rounded-[10px] opacity-0 group-hover:opacity-100 group-hover:bg-[var(--fill-tsp-white-light)] transition-opacity pointer-events-none"></div>
                <div class="flex items-center flex-1 min-w-0 gap-0.5 relative">
                  <span class="text-[13px] leading-[18px] text-[var(--text-tertiary)] font-medium min-w-0 truncate tracking-[-0.091px]">
                    {{ taskFilter === 'all' ? t('Tasks') : taskFilterLabel }}
                  </span>
                  <ChevronUp
                    :size="14"
                    class="transition-transform shrink-0 opacity-0 group-hover:opacity-100"
                    :class="tasksCollapsed ? '' : 'rotate-180'"
                    stroke="var(--icon-tertiary)" />
                </div>
                <button
                  type="button"
                  class="relative flex items-center justify-center size-[32px] rounded-[8px] clickable hover:bg-[var(--fill-tsp-white-main)] text-[var(--icon-tertiary)]"
                  :title="t('Filter')"
                  @click.stop="toggleFilterMenu">
                  <ListFilter :size="16" />
                </button>
              </div>

              <div
                v-if="showFilterMenu"
                class="absolute end-0 top-[36px] z-20 w-[200px] rounded-[12px] border border-[var(--border-dark)] bg-[var(--background-menu-white)] p-1 shadow-lg">
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

            <template v-if="!tasksCollapsed">
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
                  @pinned="handleSessionPinned"
                  @moved="handleSessionMoved" />
              </div>
              <div v-else class="flex flex-col items-center justify-center gap-4 py-8">
                <div class="flex flex-col items-center gap-2 text-[var(--text-tertiary)]">
                  <MessageSquareDashed :size="38" />
                  <span class="text-sm font-medium">{{ emptyListText }}</span>
                </div>
              </div>
            </template>
          </div>
        </div>

        <template v-else>
          <div class="mx-auto my-[10px] w-[28px] h-[1px] bg-[var(--border-main)]"></div>
          <div class="flex-1"></div>
        </template>
      </div>

      <!-- Profile footer -->
      <div
        ref="profileRef"
        class="relative flex flex-col justify-center items-start gap-[8px] bg-[var(--background-nav)] flex-shrink-0 p-[8px]">
        <div
          class="pointer-events-none absolute inset-x-0 top-[-20px] h-[24px] bg-[var(--background-nav)]"
          style="mask-image: linear-gradient(180deg, transparent 0%, #000 100%); -webkit-mask-image: linear-gradient(180deg, transparent 0%, #000 100%)"></div>
        <div v-if="showUserMenu" class="fixed z-50"
          :class="isSessionSidebarShow ? 'start-2 bottom-[52px]' : 'start-[56px] bottom-3'">
          <UserMenu />
        </div>
        <div class="flex w-full items-center justify-between pe-[2px]" :class="isSessionSidebarShow ? '' : 'flex-col-reverse gap-[4px]'">
          <div class="flex-1 min-w-0 flex items-center">
            <div
              @click="showUserMenu = !showUserMenu"
              :title="isSessionSidebarShow ? undefined : (currentUser?.fullname || t('Unknown User'))"
              class="flex min-w-0 ps-[2px] items-center gap-[8px] clickable cursor-pointer hover:opacity-70 p-[2px] text-[var(--text-primary)] text-sm font-[500]"
              aria-expanded="false" aria-haspopup="dialog">
              <div class="relative flex items-center justify-center font-bold cursor-pointer flex-shrink-0">
                <div
                  class="relative flex items-center justify-center font-bold flex-shrink-0 rounded-full overflow-hidden"
                  style="width: 28px; height: 28px; font-size: 14px; color: rgba(255, 255, 255, 0.9); background-color: rgb(59, 130, 246);">
                  {{ avatarLetter }}
                </div>
              </div>
              <span v-if="isSessionSidebarShow" class="truncate">
                {{ currentUser?.fullname || t('Unknown User') }}
              </span>
            </div>
          </div>
          <!-- Desktop / Notifications — not wired; hidden -->
        </div>
      </div>
    </div>
  </nav>
  <SearchDialog
    :visible="showSearch"
    :sessions="sessions"
    @close="showSearch = false"
    @new-task="handleNewTaskClick"
  />
</template>

<script setup lang="ts">
import {
  Bot, PanelLeft, SquarePen, MessageSquareDashed, ChevronUp, ChevronRight, Search, LibraryBig,
  Plus, FolderPlus, Check, Pin, PinOff, Folder, ListFilter, Ellipsis, Eye, Trash, Pencil,
} from 'lucide-vue-next';
import SessionItem from './SessionItem.vue';
import UserMenu from './UserMenu.vue';
import SearchDialog from './SearchDialog.vue';
import ManusLogoTextIcon from './icons/ManusLogoTextIcon.vue';
import { useSessionSidebar } from '../composables/useSessionSidebar';
import { useAuth } from '../composables/useAuth';
import { useDialog } from '../composables/useDialog';
import { useContextMenu, createMenuItem, createDangerMenuItem } from '../composables/useContextMenu';
import { ref, computed, onMounted, watch, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getSessionsSSE, getSessions } from '../api/agent';
import { getProjects, createProject, pinProject, updateProject, deleteProject } from '../api/project';
import { getCachedClientConfig } from '../api/config';
import { ListSessionItem, ProjectItem } from '../types/response';
import { useI18n } from 'vue-i18n';
import { showSuccessToast, showErrorToast } from '../utils/toast';
import { eventBus } from '../utils/eventBus';

type TaskFilter = 'all' | 'favorites' | 'shared' | 'noProject'

const { t } = useI18n()
const { isSessionSidebarShow, toggleSessionSidebar } = useSessionSidebar()
const { showInputDialog, showConfirmDialog } = useDialog()
const { showContextMenu } = useContextMenu()
const route = useRoute()
const router = useRouter()

const sessions = ref<ListSessionItem[]>([])
const projects = ref<ProjectItem[]>([])
const cancelGetSessionsSSE = ref<(() => void) | null>(null)
const isListScrolled = ref(false)
const clawEnabled = ref(false)
const scrollContainerRef = ref<HTMLElement | null>(null)
const filterMenuRef = ref<HTMLElement | null>(null)

const showSearch = ref(false)
const taskFilter = ref<TaskFilter>('all')
const showFilterMenu = ref(false)
const expandedProjectIds = ref<Set<string>>(new Set())
const pinnedCollapsed = ref(false)
const projectsCollapsed = ref(false)
const tasksCollapsed = ref(false)

const { currentUser } = useAuth()
const showUserMenu = ref(false)
const profileRef = ref<HTMLElement | null>(null)

const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)
const newTaskShortcut = computed(() => (isMac ? '⌘K' : 'Ctrl K'))

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
  return filterOptions.value.find(o => o.key === taskFilter.value)?.label || t('Tasks')
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

  // Pinned tasks float to the top within the current filter
  return [...list].sort((a, b) => Number(!!b.is_pinned) - Number(!!a.is_pinned))
})

const emptyListText = computed(() => {
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
  return sessions.value
    .filter(s => s.project_id === projectId)
    .sort((a, b) => Number(!!b.is_pinned) - Number(!!a.is_pinned))
}

/** Official selectRenderPinnedItems / unpinnedProjects */
const pinnedProjects = computed(() => projects.value.filter(p => p.is_pinned))
const unpinnedProjects = computed(() => projects.value.filter(p => !p.is_pinned))

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
  showSearch.value = false
  router.push('/')
}

const handleSearchClick = () => {
  if (!isSessionSidebarShow.value) {
    toggleSessionSidebar()
  }
  showSearch.value = true
}

const handleLibraryClick = () => {
  router.push('/library')
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
        eventBus.emit('projects:changed')
        await router.push(`/project/${project.project_id}`)
      } catch {
        showErrorToast(t('Failed to create project'))
      }
    }
  })
}

const isActiveProject = (projectId: string) => {
  return route.path === `/project/${projectId}`
}

const openProject = (projectId: string) => {
  router.push(`/project/${projectId}`)
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
    projects.value = projects.value.map(p =>
      p.project_id === updated.project_id ? updated : p,
    )
    if (updated.is_pinned) {
      pinnedCollapsed.value = false
    }
    showSuccessToast(updated.is_pinned ? t('Project pinned') : t('Project unpinned'))
  } catch {
    showErrorToast(t('Failed to update project'))
  }
}

const handleEditProject = (project: ProjectItem) => {
  showInputDialog({
    title: t('Edit project'),
    initialValue: project.name,
    placeholder: t('Enter project name'),
    confirmText: t('Save'),
    onConfirm: async (value: string) => {
      if (!value) return
      try {
        const updated = await updateProject(project.project_id, { name: value })
        projects.value = projects.value.map(p =>
          p.project_id === updated.project_id ? updated : p,
        )
        eventBus.emit('projects:changed')
        showSuccessToast(t('Project updated successfully'))
      } catch {
        showErrorToast(t('Failed to update project'))
      }
    },
  })
}

const handleDeleteProject = (project: ProjectItem) => {
  showConfirmDialog({
    title: t('Delete project?'),
    content: t('Tasks in this project will not be deleted, but they will be removed from the project.'),
    confirmText: t('Delete'),
    confirmType: 'danger',
    onConfirm: async () => {
      try {
        await deleteProject(project.project_id)
        projects.value = projects.value.filter(p => p.project_id !== project.project_id)
        sessions.value = sessions.value.map(s =>
          s.project_id === project.project_id ? { ...s, project_id: null } : s,
        )
        eventBus.emit('projects:changed')
        eventBus.emit('sessions:changed')
        showSuccessToast(t('Project deleted'))
        if (route.path === `/project/${project.project_id}`) {
          await router.push('/')
        }
      } catch {
        showErrorToast(t('Failed to update project'))
      }
    },
  })
}

/** Official project row … menu: Unpin|Pin / Edit / View project / Delete */
const handleProjectMenuClick = (event: MouseEvent, project: ProjectItem) => {
  event.stopPropagation()
  const target = event.currentTarget as HTMLElement
  const pinnedNow = !!project.is_pinned
  const items = [
    createMenuItem('pin', pinnedNow ? t('Unpin') : t('Pin'), { icon: pinnedNow ? PinOff : Pin }),
    createMenuItem('edit', t('Edit'), { icon: Pencil }),
    createMenuItem('view', t('View project'), { icon: Eye }),
    createDangerMenuItem('delete', t('Delete'), { icon: Trash }),
  ]
  showContextMenu(project.project_id, target, items, async (key: string) => {
    if (key === 'pin') {
      await handlePinProject(project)
    } else if (key === 'edit') {
      handleEditProject(project)
    } else if (key === 'view') {
      openProject(project.project_id)
    } else if (key === 'delete') {
      handleDeleteProject(project)
    }
  })
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

const handleSessionPinned = (sessionId: string, isPinned: boolean) => {
  sessions.value = sessions.value.map(session =>
    session.session_id === sessionId ? { ...session, is_pinned: isPinned } : session
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
  eventBus.on('projects:changed', loadProjects)
  eventBus.on('sessions:changed', updateSessions)

  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  if (cancelGetSessionsSSE.value) {
    cancelGetSessionsSSE.value()
    cancelGetSessionsSSE.value = null
  }

  eventBus.off('projects:changed', loadProjects)
  eventBus.off('sessions:changed', updateSessions)
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('mousedown', handleClickOutside)
})

watch(() => route.path, async () => {
  await updateSessions()
})
</script>

<style scoped>
.claw-nav-icon {
  background: url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='20'%20height='20'%20fill='none'%20viewBox='0%200%2020%2020'%20opacity='0.84'%3e%3cpath%20fill='%23333'%20fill-opacity='.9'%20fill-rule='evenodd'%20d='M5.724%204.379c3.934-3.078%207.519-2.009%208.808-.972.675.543%201.05%201.332.97%202.126-.082.823-.64%201.509-1.529%201.805-.463.155-.831.552-.998%201.034-.168.485-.1.942.144%201.24l.027.035a1%201%200%200%201%20.077.018c.265.08.413.122.617.076.202-.046.58-.215%201.13-.88l.127-.136a1.44%201.44%200%200%201%201.082-.402c.418.022.797.215%201.075.482.32.31.466.77.526%201.17.065.43.051.928-.057%201.434-.217%201.017-.837%202.142-2.09%202.82-.402.217-1.098.61-2.146.663a5%205%200%200%201-.376.504c-1.007%201.196-2.394%201.608-3.628%201.57a5.1%205.1%200%200%201-1.6-.312%203.4%203.4%200%200%201-.612.59c-.413.298-.985.518-1.667.347-1.319-.33-2.607-1.6-3.249-3.17-.344-.843-.14-1.573.285-2.087.228-.275.509-.48.777-.624a7.4%207.4%200%200%201-.33-2.307c.037-1.671.705-3.512%202.637-5.024m7.867.197c-.748-.602-3.56-1.662-6.942.985-1.551%201.213-2.034%202.618-2.061%203.874a6.1%206.1%200%200%200%20.805%203.094.75.75%200%200%201-1.29.766q-.05-.09-.103-.188a1%201%200%200%200-.203.182.47.47%200%200%200-.11.22.6.6%200%200%200%20.057.343c.515%201.26%201.491%202.1%202.225%202.285.138.035.262.008.425-.11q.096-.07.188-.167a3%203%200%200%201-.137-.145.75.75%200%200%201%201.136-.98c.294.34%201.034.704%201.948.732.877.027%201.782-.262%202.435-1.037.652-.774.809-1.508.746-2.142-.063-.632-.354-1.218-.711-1.672-.13-.103-.398-.251-.777-.376a4.1%204.1%200%200%200-1.234-.213.75.75%200%200%201%200-1.5c.469%200%20.955.077%201.4.198.017-.29.076-.576.169-.844.297-.856.974-1.644%201.942-1.966.378-.127.492-.348.51-.532.022-.213-.074-.53-.418-.807m2.527%205.25c-.675.81-1.314%201.235-1.947%201.378q-.082.017-.160.027c.093.287.16.591.192.91a4%204%200%200%201-.046%201.116c.299-.098.542-.23.763-.349.79-.428%201.19-1.134%201.336-1.812.073-.341.077-.657.04-.898-.033-.222-.087-.31-.09-.319a.3.3%200%200%200-.067-.046q-.013-.006-.021-.007'%20clip-rule='evenodd'%20/%3e%3c%2fsvg%3e") no-repeat center;
  background-size: contain;
}

:global(.dark) .claw-nav-icon {
  background-image: url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='20'%20height='20'%20fill='none'%20viewBox='0%200%2020%2020'%20opacity='0.84'%3e%3cpath%20fill='%23fff'%20fill-opacity='.9'%20fill-rule='evenodd'%20d='M5.724%204.379c3.934-3.078%207.519-2.009%208.808-.972.675.543%201.05%201.332.97%202.126-.082.823-.64%201.509-1.529%201.805-.463.155-.831.552-.998%201.034-.168.485-.1.942.144%201.24l.027.035a1%201%200%200%201%20.077.018c.265.08.413.122.617.076.202-.046.58-.215%201.13-.88l.127-.136a1.44%201.44%200%200%201%201.082-.402c.418.022.797.215%201.075.482.32.31.466.77.526%201.17.065.43.051.928-.057%201.434-.217%201.017-.837%202.142-2.09%202.82-.402.217-1.098.61-2.146.663a5%205%200%200%201-.376.504c-1.007%201.196-2.394%201.608-3.628%201.57a5.1%205.1%200%200%201-1.6-.312%203.4%203.4%200%200%201-.612.59c-.413.298-.985.518-1.667.347-1.319-.33-2.607-1.6-3.249-3.17-.344-.843-.14-1.573.285-2.087.228-.275.509-.48.777-.624a7.4%207.4%200%200%201-.33-2.307c.037-1.671.705-3.512%202.637-5.024m7.867.197c-.748-.602-3.56-1.662-6.942.985-1.551%201.213-2.034%202.618-2.061%203.874a6.1%206.1%200%200%200%20.805%203.094.75.75%200%200%201-1.29.766q-.05-.09-.103-.188a1%201%200%200%200-.203.182.47.47%200%200%200-.11.22.6.6%200%200%200%20.057.343c.515%201.26%201.491%202.1%202.225%202.285.138.035.262.008.425-.11q.096-.07.188-.167a3%203%200%200%201-.137-.145.75.75%200%200%201%201.136-.98c.294.34%201.034.704%201.948.732.877.027%201.782-.262%202.435-1.037.652-.774.809-1.508.746-2.142-.063-.632-.354-1.218-.711-1.672-.13-.103-.398-.251-.777-.376a4.1%204.1%200%200%200-1.234-.213.75.75%200%200%201%200-1.5c.469%200%20.955.077%201.4.198.017-.29.076-.576.169-.844.297-.856.974-1.644%201.942-1.966.378-.127.492-.348.51-.532.022-.213-.074-.53-.418-.807m2.527%205.25c-.675.81-1.314%201.235-1.947%201.378q-.082.017-.160.027c.093.287.16.591.192.91a4%204%200%200%201-.046%201.116c.299-.098.542-.23.763-.349.79-.428%201.19-1.134%201.336-1.812.073-.341.077-.657.04-.898-.033-.222-.087-.31-.09-.319a.3.3%200%200%200-.067-.046q-.013-.006-.021-.007'%20clip-rule='evenodd'%20/%3e%3c%2fsvg%3e");
}
</style>
