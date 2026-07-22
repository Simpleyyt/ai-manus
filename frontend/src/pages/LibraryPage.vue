<template>
  <!-- Official library shell: flex size-full min-h-0 flex-col -->
  <div class="flex size-full min-h-0 min-w-0 flex-1 flex-col bg-[var(--background-gray-main)]">
    <div
      class="flex h-[56px] w-full shrink-0 items-center justify-between py-[12px] ps-[14px] pe-[20px] md:px-[24px] gap-[8px]">
      <div class="flex-1 text-lg font-[500] leading-[28px] text-[var(--text-primary)]">
        {{ t('Library') }}
      </div>
    </div>

    <!-- Single column scroll — do not put siblings under a flex-row SimpleBar -->
    <div class="w-full flex-1 min-h-0 overflow-y-auto">
      <div class="flex min-h-full flex-col bg-[var(--background-gray-main)]">
        <!-- Sticky toolbar (official e7) -->
        <div class="w-full sticky top-0 z-10 flex flex-col bg-[var(--background-gray-main)]">
          <div class="px-5 md:px-6 bg-[var(--background-gray-main)] z-[3]">
            <div class="flex md:flex-wrap gap-[8px] pb-[12px] md:pb-[20px] items-center max-w-[1000px] mx-auto w-full">
              <div class="relative shrink-0" @click.stop>
                <button
                  type="button"
                  class="clickable flex h-8 items-center rounded-lg border text-[13px] leading-[18px] transition-colors justify-center px-2 md:justify-start md:gap-1.5 md:ps-[12px] md:pe-[8px]"
                  :class="docType !== 'all'
                    ? 'border-[var(--Button-border-secondary)] bg-[var(--fill-blue)] text-[var(--text-blue)]'
                    : 'border-[var(--Button-border-secondary)] text-[var(--text-secondary)] hover:bg-[var(--fill-tsp-white-main)]'"
                  @click="showTypeMenu = !showTypeMenu">
                  <ListFilterPlus
                    :size="16"
                    :color="docType !== 'all' ? 'var(--icon-blue)' : 'var(--icon-secondary)'"
                  />
                  <span class="hidden md:inline">{{ docTypeLabel }}</span>
                  <ChevronDown
                    :size="16"
                    class="hidden md:block"
                    :color="docType !== 'all' ? 'var(--icon-blue)' : 'var(--icon-tertiary)'"
                  />
                </button>
                <div
                  v-if="showTypeMenu"
                  class="absolute z-20 top-full mt-1 start-0 w-[200px] rounded-[12px] border border-[var(--border-main)] bg-[var(--background-menu-white)] shadow-menu py-1 overflow-hidden">
                  <button
                    v-for="opt in docTypeOptions"
                    :key="opt.value"
                    type="button"
                    class="flex w-full items-center justify-between gap-2 px-3 py-2 text-[13px] text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
                    @click="selectDocType(opt.value)">
                    <span class="flex items-center gap-2">
                      <component :is="opt.icon" :size="16" class="text-[var(--icon-secondary)]" />
                      {{ opt.label }}
                    </span>
                    <Check v-if="docType === opt.value" :size="16" />
                  </button>
                </div>
              </div>

              <button
                type="button"
                class="clickable flex h-8 items-center rounded-lg border border-[var(--Button-border-secondary)] text-[13px] transition-colors justify-center px-2 md:gap-1.5 md:px-3 shrink-0"
                :class="filterFavorites
                  ? 'bg-[var(--function-warning-tsp)] text-[var(--text-primary)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--fill-tsp-white-main)]'"
                :aria-pressed="filterFavorites"
                @click="filterFavorites = !filterFavorites">
                <Star
                  :size="16"
                  :color="filterFavorites ? 'var(--function-warning)' : 'var(--icon-secondary)'"
                  :fill="filterFavorites ? 'var(--function-warning)' : 'none'"
                />
                <span class="hidden md:inline">{{ t('My favorites') }}</span>
              </button>

              <div
                class="order-first w-full md:order-none md:w-auto md:ms-auto md:min-w-[160px] md:max-w-[200px] border border-[var(--Button-border-secondary)] bg-transparent rounded-[8px] h-8 flex items-center gap-[10px] py-1 ps-3 pe-1.5"
                :class="searchFocused ? 'border-[var(--border-primary)]' : ''">
                <Search :size="16" class="shrink-0 text-[var(--icon-secondary)]" />
                <input
                  v-model="searchQuery"
                  type="text"
                  class="h-full min-w-0 flex-1 bg-transparent outline-none text-sm text-[var(--text-primary)] placeholder:text-[var(--text-disable)]"
                  :placeholder="t('Search files')"
                  @focus="searchFocused = true"
                  @blur="searchFocused = false"
                />
              </div>

              <div class="shrink-0 flex items-center h-8">
                <button
                  type="button"
                  class="h-full w-[32px] min-w-[32px] flex items-center justify-center"
                  :title="t('Grid view')"
                  @click="viewMode = 'grid'">
                  <LayoutGrid
                    :size="16"
                    :color="viewMode === 'grid' ? 'var(--icon-primary)' : 'var(--icon-tertiary)'"
                  />
                </button>
                <button
                  type="button"
                  class="h-full w-[32px] min-w-[32px] flex items-center justify-center"
                  :title="t('List view')"
                  @click="viewMode = 'list'">
                  <List
                    :size="16"
                    :color="viewMode === 'list' ? 'var(--icon-primary)' : 'var(--icon-tertiary)'"
                  />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="loading" class="py-16 text-center text-sm text-[var(--text-tertiary)]">
          {{ t('Loading...') }}
        </div>
        <div
          v-else-if="isEmpty"
          class="py-16 text-center text-sm text-[var(--text-tertiary)]">
          {{ filterFavorites ? t('No favorite files') : t('No files in library') }}
        </div>

        <!-- Official eT: flat file grid when search / favorites / type filter -->
        <div
          v-else-if="browseMode === 'file'"
          class="flex flex-col pb-6 px-[20px] mt-[12px]">
          <div class="max-w-[1000px] mx-auto w-full">
            <div
              v-if="viewMode === 'grid'"
              class="grid gap-3 items-start grid-cols-1 md:grid-cols-3">
              <LibraryFileCard
                v-for="(file, idx) in filteredFiles"
                :key="`${file.session_id}-${file.file_id || idx}`"
                :file="file"
                view-mode="grid"
                @open="openSession(file.session_id)"
              />
            </div>
            <div v-else class="flex flex-col">
              <LibraryFileCard
                v-for="(file, idx) in filteredFiles"
                :key="`${file.session_id}-${file.file_id || idx}`"
                :file="file"
                view-mode="list"
                @open="openSession(file.session_id)"
              />
            </div>
          </div>
        </div>

        <!-- Official eW: session-grouped when browsing All -->
        <div
          v-else
          class="flex flex-col pb-6 px-[20px]"
          :class="viewMode === 'grid' ? 'gap-3' : 'gap-[17px]'">
          <div class="max-w-[1000px] mx-auto w-full flex flex-col md:gap-[24px] gap-[12px]">
            <section
              v-for="group in groups"
              :key="group.sessionId"
              class="flex flex-col"
              :class="viewMode === 'grid' ? 'md:gap-[12px] gap-[8px]' : ''">
              <div
                class="flex items-center pt-[12px]"
                :class="viewMode === 'grid'
                  ? 'justify-between gap-[8px]'
                  : 'gap-[12px] md:pb-[8px] pb-[6px] md:ps-[6px]'">
                <button
                  type="button"
                  class="min-w-0 truncate md:text-[16px] text-[14px] font-medium leading-[22px] text-[var(--text-primary)] hover:underline text-left"
                  :class="viewMode === 'list' ? 'flex-1' : ''"
                  @click="openSession(group.sessionId)">
                  {{ group.title }}
                </button>
                <span
                  v-if="group.timeLabel"
                  class="text-[13px] leading-[18px] text-[var(--text-secondary)] flex-shrink-0">
                  {{ group.timeLabel }}
                </span>
              </div>

              <div
                v-if="viewMode === 'grid'"
                class="grid gap-3 items-start grid-cols-1 md:grid-cols-3">
                <LibraryFileCard
                  v-for="(file, idx) in visibleFiles(group)"
                  :key="`${file.session_id}-${file.file_id || idx}`"
                  :file="file"
                  view-mode="grid"
                  @open="openSession(file.session_id)"
                />
              </div>
              <template v-else>
                <LibraryFileCard
                  v-for="(file, idx) in group.files"
                  :key="`${file.session_id}-${file.file_id || idx}`"
                  :file="file"
                  view-mode="list"
                  @open="openSession(file.session_id)"
                />
              </template>

              <button
                v-if="viewMode === 'grid' && !expandedIds.has(group.sessionId) && group.files.length > 3"
                type="button"
                class="clickable flex items-center gap-[6px] px-[12px] py-[4px] hover:opacity-80 rounded-[999px] border border-[var(--border-main)] w-fit"
                @click="expandGroup(group.sessionId)">
                <span class="text-[13px] leading-[18px] text-[var(--text-tertiary)]">
                  {{ t('{count} more files', { count: group.files.length - 3 }) }}
                </span>
                <ChevronDown :size="16" color="var(--text-tertiary)" />
              </button>
            </section>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Check, ChevronDown, CircleEllipsis, FileText, Image as ImageIcon,
  LayoutGrid, List, ListFilterPlus, Search, Star,
} from 'lucide-vue-next'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { getLibraryFiles } from '../api/project'
import LibraryFileCard from '../components/LibraryFileCard.vue'
import type { LibraryFileItem } from '../types/response'
import { formatCustomTime } from '../utils/time'

type ViewMode = 'grid' | 'list'
type DocType = 'all' | 'documents' | 'media' | 'others'

interface LibraryGroup {
  sessionId: string
  title: string
  timeLabel: string
  latestAt: number
  files: LibraryFileItem[]
}

const { t, locale } = useI18n()
const router = useRouter()

const files = ref<LibraryFileItem[]>([])
const loading = ref(false)
const searchQuery = ref('')
const searchFocused = ref(false)
const filterFavorites = ref(false)
const viewMode = ref<ViewMode>('grid')
const docType = ref<DocType>('all')
const showTypeMenu = ref(false)
const expandedIds = ref(new Set<string>())

const docTypeOptions = computed(() => [
  { value: 'all' as DocType, label: t('All'), icon: ListFilterPlus },
  { value: 'documents' as DocType, label: t('Documents'), icon: FileText },
  { value: 'media' as DocType, label: t('Images & Videos'), icon: ImageIcon },
  { value: 'others' as DocType, label: t('Others'), icon: CircleEllipsis },
])

const docTypeLabel = computed(
  () => docTypeOptions.value.find((o) => o.value === docType.value)?.label || t('All'),
)

const extOf = (f: LibraryFileItem) => {
  const name = f.filename || f.file_path || ''
  const i = name.lastIndexOf('.')
  return i > 0 ? name.slice(i + 1).toLowerCase() : ''
}

const isMediaFile = (f: LibraryFileItem) => {
  const e = extOf(f)
  const ct = f.content_type || ''
  return ct.startsWith('image/') || ct.startsWith('video/')
    || ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'mp4', 'mov', 'webm'].includes(e)
}

const isDocumentFile = (f: LibraryFileItem) =>
  ['pdf', 'doc', 'docx', 'txt', 'md', 'rtf', 'pages'].includes(extOf(f))

const matchDocType = (f: LibraryFileItem) => {
  if (docType.value === 'all') return true
  if (docType.value === 'media') return isMediaFile(f)
  if (docType.value === 'documents') return isDocumentFile(f)
  return !isMediaFile(f) && !isDocumentFile(f)
}

const filteredFiles = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return files.value.filter((f) => {
    if (filterFavorites.value && !f.is_favorite) return false
    if (!matchDocType(f)) return false
    if (!q) return true
    const name = (f.filename || f.file_path || '').toLowerCase()
    const title = (f.session_title || '').toLowerCase()
    return name.includes(q) || title.includes(q)
  })
})

/** Official: type/favorite/search → flat "file" mode; else session-grouped */
const browseMode = computed<'file' | 'session'>(() =>
  docType.value !== 'all' || filterFavorites.value || searchQuery.value.trim()
    ? 'file'
    : 'session',
)

const groups = computed((): LibraryGroup[] => {
  const map = new Map<string, LibraryGroup>()
  for (const file of filteredFiles.value) {
    let group = map.get(file.session_id)
    if (!group) {
      const latestAt = file.latest_message_at || 0
      group = {
        sessionId: file.session_id,
        title: file.session_title || t('Untitled task'),
        timeLabel: latestAt ? formatCustomTime(latestAt, t, locale.value) : '',
        latestAt,
        files: [],
      }
      map.set(file.session_id, group)
    }
    group.files.push(file)
  }
  return [...map.values()].sort((a, b) => b.latestAt - a.latestAt)
})

const isEmpty = computed(() =>
  browseMode.value === 'file'
    ? filteredFiles.value.length === 0
    : groups.value.length === 0,
)

const visibleFiles = (group: LibraryGroup) =>
  expandedIds.value.has(group.sessionId) ? group.files : group.files.slice(0, 3)

const selectDocType = (value: DocType) => {
  docType.value = value
  showTypeMenu.value = false
}

const expandGroup = (sessionId: string) => {
  const next = new Set(expandedIds.value)
  next.add(sessionId)
  expandedIds.value = next
}

const onDocClick = () => {
  showTypeMenu.value = false
}

const load = async () => {
  loading.value = true
  try {
    const res = await getLibraryFiles()
    files.value = res.files
  } catch (e) {
    console.error(e)
    files.value = []
  } finally {
    loading.value = false
  }
}

const openSession = (sessionId: string) => {
  router.push(`/chat/${sessionId}`)
}

onMounted(() => {
  load()
  document.addEventListener('click', onDocClick)
})
onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
})
</script>
