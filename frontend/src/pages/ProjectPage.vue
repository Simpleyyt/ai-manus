<template>
  <!-- Official: LifeCycle → Dragger → InfiniteScroll → SimpleBar → A9 + @container grid (1whdjijd45ufa.js bF) -->
  <div class="flex flex-col items-center gap-3 w-full h-full relative min-h-0 min-w-0 flex-1 bg-[var(--background-gray-main)]">
    <div class="flex w-full flex-1 min-h-0 flex-col overflow-y-auto overflow-x-hidden">
      <!-- A9 / uM sticky header (Share skipped per product constraints) -->
      <div class="sticky top-0 z-10 flex h-[56px] w-full shrink-0 items-center justify-between bg-[var(--background-gray-main)] py-[12px] ps-[14px] pe-[20px] md:px-[24px]">
        <div class="flex items-center" />
        <div class="relative flex items-center gap-[4px]" @click.stop>
          <button
            type="button"
            class="flex size-[28px] items-center justify-center rounded-[8px] hover:bg-[var(--fill-tsp-white-main)]"
            :title="t('More')"
            @click="showMoreMenu = !showMoreMenu">
            <Ellipsis :size="18" class="text-[var(--icon-secondary)]" />
          </button>
          <div
            v-if="showMoreMenu"
            class="absolute end-0 top-full z-20 mt-1 min-w-[180px] overflow-hidden rounded-[12px] border border-[var(--border-main)] bg-[var(--background-menu-white)] py-1 shadow-menu">
            <button
              type="button"
              class="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
              @click="openRename">
              <Pencil :size="16" class="text-[var(--icon-secondary)]" />
              {{ t('Edit project') }}
            </button>
            <button
              type="button"
              class="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
              @click="openInstructions">
              <ScrollText :size="16" class="text-[var(--icon-secondary)]" />
              {{ t('Edit instructions') }}
            </button>
            <button
              type="button"
              class="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[var(--function-error)] hover:bg-[var(--fill-tsp-white-main)]"
              @click="confirmDelete">
              <Trash2 :size="16" color="currentColor" />
              {{ t('Delete project') }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="loadError" class="py-16 text-center text-sm text-[var(--text-tertiary)]">
        {{ loadError }}
      </div>

      <div v-else-if="!project" class="py-16 text-center text-sm text-[var(--text-tertiary)]">
        {{ t('Loading...') }}
      </div>

      <div v-else class="flex-1 min-h-0 w-full">
        <!-- Official grid; local Tailwind uses viewport md: (no @md container queries) -->
        <div
          class="grid grid-cols-1 pt-8 px-[24px] mx-auto w-full max-w-[768px] md:px-[18px] md:h-full md:max-w-[1168px] md:grid-cols-[minmax(390px,768px)_minmax(240px,320px)] md:gap-x-[44px] md:grid-rows-[auto_auto_1fr]">
          <!-- AX project title -->
          <div class="flex gap-[12px] items-center">
            <div
              class="shrink-0 p-[12px] flex items-center justify-center rounded-[12px] bg-[var(--fill-tsp-white-main)] hover:bg-[var(--fill-tsp-white-light)] clickable"
              @click="openRename">
              <Folder :size="24" color="var(--icon-primary)" />
            </div>
            <div class="min-w-0 flex-1 truncate space-y-1">
              <div
                class="w-fit text-[var(--text-primary)] text-xl font-[500] break-words whitespace-pre-wrap cursor-pointer hover:opacity-80"
                @click="openRename">
                {{ project.name }}
              </div>
              <div class="flex items-center gap-[8px] text-[var(--text-tertiary)] text-xs truncate">
                <span class="overflow-hidden text-ellipsis">
                  {{ t('Created by {name}', { name: creatorName }) }}
                </span>
                <template v-if="updatedLabel">
                  <div class="size-[3px] shrink-0 rounded-full bg-[var(--icon-disable)]" />
                  <span class="overflow-hidden text-ellipsis">
                    {{ t('Updated {date}', { date: updatedLabel }) }}
                  </span>
                </template>
              </div>
            </div>
          </div>

          <!-- gN scene=project — reuse ChatBox (same chrome as home) -->
          <div class="mt-[24px] w-full flex flex-col md:col-start-1">
            <div class="flex flex-col w-full bg-[var(--background-gray-main)]">
              <div class="bg-[var(--background-gray-main)] rounded-[22px_22px_0px_0px]" />
              <ChatBox
                v-model="draft"
                v-model:attachments="attachments"
                :rows="2"
                :is-running="false"
                :placeholder="t('Give Manus a task...')"
                @submit="handleNewTask"
              />
            </div>
          </div>

          <!-- Right column: AJ Instructions (+ official also has Skills/Scheduled — skipped MVP) -->
          <div class="mt-[24px] space-y-4 md:col-start-2 md:row-[1/4] md:mt-0">
            <!-- AJ -->
            <div class="w-full rounded-[12px] border border-[var(--border-main)] overflow-hidden">
              <div
                class="space-y-[8px] p-4 pe-3 clickable hover:bg-[var(--fill-tsp-white-light)]"
                @click="openInstructions">
                <div class="flex items-center justify-between">
                  <div class="flex gap-[2px] items-center min-w-0">
                    <span class="text-[var(--text-primary)] text-sm font-[500] truncate">
                      {{ t('Instructions') }}
                    </span>
                    <ChevronRight :size="16" color="var(--icon-secondary)" class="shrink-0" />
                  </div>
                </div>
                <p class="text-[var(--text-tertiary)] text-[13px] leading-[18px] md:line-clamp-3 md:whitespace-pre-wrap break-words truncate">
                  {{ project.instruction?.trim() || t('Guide how Manus responds across all tasks in this project.') }}
                </p>
                <button
                  v-if="!project.instruction?.trim()"
                  type="button"
                  class="inline-flex items-center gap-1 rounded-[8px] border border-[var(--border-btn-main)] bg-[var(--Button-secondary-main)] px-2.5 py-1 text-[13px] text-[var(--text-secondary)] hover:bg-[var(--fill-tsp-white-dark)]"
                  @click.stop="openInstructions">
                  <Plus :size="16" color="var(--icon-secondary)" />
                  {{ t('Add') }}
                </button>
              </div>
            </div>
          </div>

          <!-- bL Tasks -->
          <div class="mt-[32px] pb-[32px] px-[16px] w-full md:col-start-1">
            <div class="mx-auto relative w-full">
              <div class="w-full mb-1">
                <span class="text-[var(--text-primary)] text-base font-[500]">{{ t('Tasks') }}</span>
                <p class="text-[var(--text-disable)] text-[13px]">
                  {{ t('Your tasks stay private unless shared') }}
                </p>
              </div>

              <div v-if="loadingSessions" class="py-8 text-center text-sm text-[var(--text-tertiary)]">
                {{ t('Loading...') }}
              </div>

              <div
                v-else-if="projectSessions.length === 0"
                class="flex flex-col items-center gap-3 pt-48 pb-6">
                <MessageSquareDashed :size="32" color="var(--text-disable)" />
                <span class="text-[var(--text-tertiary)] text-sm text-center">
                  {{ t('Create a new task to get started') }}
                </span>
              </div>

              <div v-else class="flex flex-col">
                <SessionItem
                  v-for="session in projectSessions"
                  :key="session.session_id"
                  variant="project"
                  :session="session"
                  :projects="projectsList"
                  @deleted="handleSessionDeleted"
                  @renamed="handleSessionRenamed"
                  @shared="noop"
                  @favorited="handleSessionFavorited"
                  @moved="handleSessionMoved"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Instructions dialog — official w-[560px] h-[560px] -->
    <div
      v-if="showInstructions"
      class="fixed inset-0 z-[1000] flex items-center justify-center">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-[4px]" @click="closeInstructions" />
      <div
        role="dialog"
        class="relative z-10 flex h-[560px] max-h-[95%] w-[560px] max-w-[95%] flex-col overflow-hidden rounded-[20px] border border-white/5 bg-[var(--background-menu-white)]">
        <div class="flex items-center justify-between gap-2 border-b border-[var(--border-main)] px-[16px] pt-[16px] pb-[8px]">
          <div class="min-w-0 flex flex-col flex-1 space-y-3 overflow-hidden pb-[2px]">
            <h3 class="text-[14px] font-[500] leading-[20px] text-[var(--text-primary)]">
              {{ t('Project instructions') }}
            </h3>
            <p class="text-[var(--text-secondary)] text-[14px]">
              {{ t('Applies to all new messages in this project.') }}
            </p>
          </div>
          <button
            type="button"
            class="flex size-[28px] shrink-0 items-center justify-center rounded-md hover:bg-[var(--fill-tsp-gray-main)]"
            :aria-label="t('Close Dialog')"
            @click="closeInstructions">
            <X :size="18" class="text-[var(--icon-tertiary)]" />
          </button>
        </div>
        <div class="flex min-h-0 flex-1 flex-col px-[16px] py-3">
          <textarea
            v-model="instructionDraft"
            class="p-[8px] px-[12px] flex-1 min-h-[120px] rounded-[8px] bg-[var(--fill-tsp-white-light)] w-full placeholder:text-[var(--text-disable)] text-sm leading-[20px] text-[var(--text-primary)] outline-none resize-none"
            :placeholder="instructionPlaceholder"
          />
        </div>
        <div class="flex shrink-0 items-center justify-end gap-[8px] border-t border-[var(--border-main)] p-[16px]">
            <button
              type="button"
              class="rounded-[10px] border border-[var(--border-btn-main)] bg-[var(--Button-secondary-main)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--fill-tsp-white-dark)]"
              @click="closeInstructions">
              {{ t('Cancel') }}
            </button>
            <button
              type="button"
              class="rounded-[10px] bg-[var(--Button-primary-black)] px-3 py-2 text-sm text-[var(--text-onblack)] hover:opacity-90 disabled:opacity-50"
              :disabled="savingInstruction"
              @click="saveInstructions">
              {{ t('Save') }}
            </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ChevronRight, Ellipsis, Folder, MessageSquareDashed, Pencil, Plus, ScrollText, Trash2, X,
} from 'lucide-vue-next'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { createSession, getSessions, moveSessionProject } from '../api/agent'
import {
  deleteProject, getProject, getProjects, updateProject,
} from '../api/project'
import type { FileInfo } from '../api/file'
import ChatBox from '../components/ChatBox.vue'
import SessionItem from '../components/SessionItem.vue'
import { useAuth } from '../composables/useAuth'
import { useDialog } from '../composables/useDialog'
import type { ListSessionItem, ProjectItem } from '../types/response'
import { eventBus } from '../utils/eventBus'
import { formatCustomTime } from '../utils/time'
import { showErrorToast, showSuccessToast } from '../utils/toast'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const { currentUser } = useAuth()
const { showConfirmDialog, showInputDialog } = useDialog()

const projectId = computed(() => route.params.projectId as string)

const project = ref<ProjectItem | null>(null)
const projectsList = ref<ProjectItem[]>([])
const sessions = ref<ListSessionItem[]>([])
const loadingSessions = ref(false)
const loadError = ref('')
const creatingTask = ref(false)
const draft = ref('')
const attachments = ref<FileInfo[]>([])
const showMoreMenu = ref(false)
const showInstructions = ref(false)
const instructionDraft = ref('')
const savingInstruction = ref(false)

const projectSessions = computed(() =>
  sessions.value.filter((s) => s.project_id === projectId.value),
)

const creatorName = computed(() => currentUser.value?.fullname || t('Unknown User'))

const updatedLabel = computed(() => {
  const raw = project.value?.updated_at
  if (!raw) return ''
  const ts = Math.floor(new Date(raw).getTime() / 1000)
  if (Number.isNaN(ts)) return ''
  return formatCustomTime(ts, t, locale.value)
})

const instructionPlaceholder = computed(() =>
  t('Keep responses concise and professional.\nUse our brand voice from the attached guidelines.\nAlways provide sources for important conclusions.\nNever publish without approval.'),
)

const noop = () => {}

const closeMenus = () => {
  showMoreMenu.value = false
}

const loadProject = async () => {
  loadError.value = ''
  try {
    project.value = await getProject(projectId.value)
  } catch (e) {
    console.error(e)
    project.value = null
    loadError.value = t('Project not found')
  }
}

const loadSessions = async () => {
  loadingSessions.value = true
  try {
    const res = await getSessions()
    sessions.value = res.sessions
  } catch (e) {
    console.error(e)
    sessions.value = []
  } finally {
    loadingSessions.value = false
  }
}

const loadProjectsList = async () => {
  try {
    const res = await getProjects()
    projectsList.value = res.projects
  } catch {
    projectsList.value = project.value ? [project.value] : []
  }
}

const refreshAll = async () => {
  draft.value = ''
  attachments.value = []
  await Promise.all([loadProject(), loadSessions(), loadProjectsList()])
}

const handleNewTask = async () => {
  if ((!draft.value.trim() && attachments.value.length === 0) || creatingTask.value || !project.value) return
  creatingTask.value = true
  try {
    const session = await createSession()
    await moveSessionProject(session.session_id, project.value.project_id)
    eventBus.emit('sessions:changed')
    eventBus.emit('projects:changed')
    const message = draft.value
    const files = attachments.value.map((file: FileInfo) => ({
      file_id: file.file_id,
      filename: file.filename,
      content_type: file.content_type,
      size: file.size,
      upload_date: file.upload_date,
    }))
    await router.push({
      path: `/chat/${session.session_id}`,
      state: { message, files },
    })
  } catch (e) {
    console.error(e)
    showErrorToast(t('Failed to create task'))
    creatingTask.value = false
  }
}

const openRename = () => {
  showMoreMenu.value = false
  if (!project.value) return
  showInputDialog({
    title: t('Edit project'),
    initialValue: project.value.name,
    placeholder: t('Enter project name'),
    confirmText: t('Save'),
    onConfirm: async (value) => {
      if (!value || !project.value) return
      try {
        project.value = await updateProject(project.value.project_id, { name: value })
        eventBus.emit('projects:changed')
        showSuccessToast(t('Project updated successfully'))
      } catch (e) {
        console.error(e)
        showErrorToast(t('Failed to update project'))
      }
    },
  })
}

const openInstructions = () => {
  showMoreMenu.value = false
  instructionDraft.value = project.value?.instruction || ''
  showInstructions.value = true
}

const closeInstructions = () => {
  showInstructions.value = false
}

const saveInstructions = async () => {
  if (!project.value || savingInstruction.value) return
  savingInstruction.value = true
  try {
    project.value = await updateProject(project.value.project_id, {
      instruction: instructionDraft.value,
    })
    eventBus.emit('projects:changed')
    showSuccessToast(t('Project updated successfully'))
    showInstructions.value = false
  } catch (e) {
    console.error(e)
    showErrorToast(t('Failed to update project'))
  } finally {
    savingInstruction.value = false
  }
}

const confirmDelete = () => {
  showMoreMenu.value = false
  if (!project.value) return
  showConfirmDialog({
    title: t('Delete project?'),
    content: t('Tasks in this project will not be deleted, but they will be removed from the project.'),
    confirmText: t('Delete'),
    confirmType: 'danger',
    onConfirm: async () => {
      try {
        await deleteProject(project.value!.project_id)
        eventBus.emit('projects:changed')
        eventBus.emit('sessions:changed')
        showSuccessToast(t('Project deleted'))
        await router.push('/')
      } catch (e) {
        console.error(e)
        showErrorToast(t('Failed to update project'))
      }
    },
  })
}

const handleSessionDeleted = (sessionId: string) => {
  sessions.value = sessions.value.filter((s) => s.session_id !== sessionId)
  eventBus.emit('sessions:changed')
}

const handleSessionRenamed = (sessionId: string, title: string) => {
  sessions.value = sessions.value.map((s) =>
    s.session_id === sessionId ? { ...s, title } : s,
  )
  eventBus.emit('sessions:changed')
}

const handleSessionFavorited = (sessionId: string, isFavorite: boolean) => {
  sessions.value = sessions.value.map((s) =>
    s.session_id === sessionId ? { ...s, is_favorite: isFavorite } : s,
  )
}

const handleSessionMoved = (sessionId: string, nextProjectId: string | null) => {
  sessions.value = sessions.value.map((s) =>
    s.session_id === sessionId ? { ...s, project_id: nextProjectId } : s,
  )
  eventBus.emit('sessions:changed')
  eventBus.emit('projects:changed')
}

watch(projectId, () => {
  refreshAll()
})

onMounted(() => {
  refreshAll()
  document.addEventListener('click', closeMenus)
  eventBus.on('sessions:changed', loadSessions)
  eventBus.on('projects:changed', loadProjectsList)
})

onUnmounted(() => {
  document.removeEventListener('click', closeMenus)
  eventBus.off('sessions:changed', loadSessions)
  eventBus.off('projects:changed', loadProjectsList)
})
</script>
