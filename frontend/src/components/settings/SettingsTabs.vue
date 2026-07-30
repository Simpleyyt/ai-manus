<script setup lang="ts">
import { ref, computed, watch, type Component } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Settings2,
  UserRound,
  Keyboard,
  LayoutGrid,
  CircleHelp,
  Search,
  ChevronsUpDown,
  ArrowUpRight,
} from 'lucide-vue-next'
import { useAuth } from '@/composables/useAuth'
import { useSettingsDialog } from '@/composables/useSettingsDialog'

export type SettingsTabId =
  | 'general'
  | 'account'
  | 'shortcuts'
  | 'personalization'
  | 'help'

export interface SettingsNavItem {
  id: SettingsTabId
  label: string
  icon: Component
  external?: boolean
}

export interface SettingsNavGroup {
  id: string
  label?: string
  items: SettingsNavItem[]
}

interface Props {
  defaultTab?: string
}

const props = withDefaults(defineProps<Props>(), {
  defaultTab: 'general',
})

const emit = defineEmits<{
  tabChange: [tabId: SettingsTabId]
}>()

const { t } = useI18n()
const { currentUser } = useAuth()
const { isSettingsDialogOpen } = useSettingsDialog()

const navGroups: SettingsNavGroup[] = [
  {
    id: 'settings',
    label: 'Settings',
    items: [
      { id: 'general', label: 'General', icon: Settings2 },
      { id: 'account', label: 'Account', icon: UserRound },
      { id: 'shortcuts', label: 'Shortcuts', icon: Keyboard },
    ],
  },
  {
    id: 'features',
    label: 'Features',
    items: [
      { id: 'personalization', label: 'Personalization', icon: LayoutGrid },
    ],
  },
]

const helpItem: SettingsNavItem = {
  id: 'help',
  label: 'Get help',
  icon: CircleHelp,
  external: true,
}

const activeTab = ref<SettingsTabId>(
  (props.defaultTab as SettingsTabId) || 'general',
)
const searchQuery = ref('')

watch(
  () => props.defaultTab,
  (tab) => {
    if (tab && tab !== activeTab.value) {
      activeTab.value = tab as SettingsTabId
    }
  },
)

watch(isSettingsDialogOpen, (open) => {
  if (open && props.defaultTab) {
    activeTab.value = props.defaultTab as SettingsTabId
  }
})

const avatarLetter = computed(() =>
  currentUser.value?.fullname?.charAt(0)?.toUpperCase() || 'M',
)

const filteredGroups = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return navGroups
  return navGroups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) =>
        t(item.label).toLowerCase().includes(q)
        || item.label.toLowerCase().includes(q),
      ),
    }))
    .filter((group) => group.items.length > 0)
})

const showHelp = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return true
  return t(helpItem.label).toLowerCase().includes(q)
    || helpItem.label.toLowerCase().includes(q)
})

const activeTitle = computed(() => {
  const all = [...navGroups.flatMap((g) => g.items), helpItem]
  const current = all.find((item) => item.id === activeTab.value)
  return current ? t(current.label) : ''
})

const setActiveTab = (tabId: SettingsTabId) => {
  activeTab.value = tabId
  emit('tabChange', tabId)
}

defineExpose({ activeTab })
</script>

<template>
  <div class="flex h-[min(580px,calc(100vh-82px))] flex-col md:h-[90vh] md:flex-row">
    <!-- Sidebar -->
    <div
      class="md:w-[221px] overflow-x-auto md:overflow-x-visible md:border-r border-[var(--border-main)] pb-2 md:pb-0 relative flex flex-col"
    >
      <h3
        class="block md:hidden self-stretch pt-4 md:pt-5 px-4 md:px-5 pb-2 text-[18px] font-semibold leading-7 text-[var(--text-primary)] sticky left-0"
      >
        {{ t('Settings') }}
      </h3>

      <!-- User card -->
      <div class="px-3 py-1 mt-[6px] hidden md:block">
        <div class="group grid ps-1 pe-1 pt-4 pb-[10px] w-full cursor-default">
          <div
            class="col-start-1 row-start-1 min-w-0 min-h-[36px] flex gap-2 items-center"
          >
            <div class="flex flex-1 gap-[10px] items-center overflow-hidden min-w-0">
              <div
                class="relative flex items-center justify-center font-bold flex-shrink-0 rounded-full overflow-hidden"
                style="width: 28px; height: 28px; font-size: 14px; color: rgba(255, 255, 255, 0.9); background-color: rgb(59, 130, 246);"
              >
                {{ avatarLetter }}
              </div>
              <div class="flex min-w-0 flex-1 flex-col justify-center">
                <span
                  class="truncate text-[14px] font-medium leading-5 tracking-[-0.15px] text-[var(--text-primary)]"
                >
                  {{ currentUser?.fullname || t('Unknown User') }}
                </span>
                <span class="truncate text-[12px] leading-4 text-[var(--text-tertiary)]">
                  {{ t('Personal') }}
                </span>
              </div>
            </div>
            <div class="p-1 rounded-[6px] flex-shrink-0">
              <ChevronsUpDown class="shrink-0" :size="16" color="var(--icon-tertiary)" />
            </div>
          </div>
        </div>
      </div>

      <!-- Search -->
      <div class="px-3 pt-1 pb-2 hidden md:block">
        <div
          class="flex h-9 items-center gap-2 rounded-lg border border-[var(--Button-border-secondary)] focus-within:border-[var(--border-input-active)] ps-[11px] pe-2"
        >
          <Search class="shrink-0" :size="16" color="var(--icon-tertiary)" />
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="t('Search')"
            class="min-w-0 flex-1 bg-transparent text-[14px] leading-5 tracking-[-0.15px] text-[var(--text-primary)] outline-none placeholder:text-[var(--text-disable)]"
          >
        </div>
      </div>

      <!-- Nav -->
      <div class="relative flex-1 w-full min-h-0 overflow-y-auto">
        <div class="relative flex w-full max-md:pe-3">
          <div
            class="flex-1 flex-shrink-0 flex items-start self-stretch px-3 overflow-auto w-max md:w-full pb-0 border-b border-[var(--border-main)] md:border-b-0 md:flex-col max-md:gap-[10px]"
          >
            <template v-for="group in filteredGroups" :key="group.id">
              <div
                v-if="group.label"
                class="hidden md:block text-[var(--text-tertiary)] text-[13px] leading-[18px] pt-3 pr-3 pl-3.5 pb-1"
              >
                {{ t(group.label) }}
              </div>
              <div class="flex md:gap-[2px] gap-[10px] md:flex-col items-start self-stretch w-full">
                <button
                  v-for="item in group.items"
                  :key="item.id"
                  type="button"
                  :class="[
                    'flex max-md:px-1 py-2 items-center text-[14px] leading-5 text-[var(--text-primary)] max-md:whitespace-nowrap md:h-8 md:gap-2 md:self-stretch md:ps-3.5 md:pe-4 md:rounded-lg w-full',
                    activeTab === item.id
                      ? 'md:bg-[var(--fill-tsp-white-main)] font-medium border-b-[2px] md:border-none border-[var(--Button-black)]'
                      : 'hover:bg-[var(--fill-tsp-white-light)]',
                    'hover:active:bg-[var(--fill-tsp-white-dark)]',
                  ]"
                  @click="setActiveTab(item.id)"
                >
                  <span
                    class="hidden md:block"
                    :class="activeTab === item.id ? 'text-[var(--icon-primary)]' : 'text-[var(--icon-secondary)]'"
                  >
                    <component :is="item.icon" class="w-4 h-4" />
                  </span>
                  <span class="truncate">{{ t(item.label) }}</span>
                </button>
              </div>
            </template>

            <template v-if="showHelp">
              <div class="hidden md:block self-stretch px-2.5 my-2">
                <div class="h-[1px] bg-[var(--border-primary)]" />
              </div>
              <div class="flex md:flex-col items-start self-stretch w-full">
                <button
                  type="button"
                  :class="[
                    'flex max-md:px-1 py-2 items-center text-[14px] leading-5 text-[var(--text-primary)] max-md:whitespace-nowrap md:h-8 md:gap-2 md:self-stretch md:ps-3.5 md:pe-4 md:rounded-lg w-full',
                    activeTab === 'help'
                      ? 'md:bg-[var(--fill-tsp-white-main)] font-medium'
                      : 'hover:bg-[var(--fill-tsp-white-light)]',
                  ]"
                  @click="setActiveTab('help')"
                >
                  <span
                    class="hidden md:block"
                    :class="activeTab === 'help' ? 'text-[var(--icon-primary)]' : 'text-[var(--icon-secondary)]'"
                  >
                    <CircleHelp class="w-4 h-4" />
                  </span>
                  <span class="truncate flex-1 text-start">{{ t(helpItem.label) }}</span>
                  <ArrowUpRight
                    class="hidden md:block shrink-0"
                    :size="16"
                    color="var(--icon-tertiary)"
                  />
                </button>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex flex-col flex-1 min-h-0 overflow-hidden">
      <div class="flex flex-col flex-1 min-h-full px-4 md:px-6 overflow-y-auto">
        <div class="relative flex flex-col items-start self-stretch min-h-full flex-1 w-full md:max-w-[768px] md:mx-auto">
          <div class="relative z-[1] flex flex-col items-start self-stretch min-h-full flex-1 w-full">
            <div class="gap-1 items-center pt-[34px] pb-4 hidden md:flex self-stretch border-b border-[var(--border-main)]">
              <div class="flex-1 max-w-full">
                <h1 class="flex items-center gap-2 text-[var(--text-primary)] text-2xl font-[600] leading-[30px] max-w-full">
                  {{ activeTitle }}
                </h1>
              </div>
            </div>
            <div class="space-y-6 self-stretch flex-1 pt-2 pb-4 md:pt-6 w-full">
              <slot :name="activeTab" :active-tab="activeTab" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
