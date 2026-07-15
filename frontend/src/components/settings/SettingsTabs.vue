<template>
  <div class="flex flex-col md:flex-row h-[580px] md:h-[672px] max-h-[90vh]">
    <!-- Tab Sidebar -->
    <div
      class="md:w-[221px] overflow-x-auto md:overflow-x-visible border-r border-[var(--border-main)] pb-2 md:pb-0 relative">
      <div class="items-center hidden px-5 pt-5 pb-3 md:flex">
        <div class="flex gap-0.5 w-fit">
          <ManusLogoIcon :width="22.9" :height="30" />
          <ManusLogoTextIcon width="69.47368421052632" height="30" />
        </div>
      </div>
      <h3
        class="block md:hidden self-stretch pt-4 md:pt-5 px-4 md:px-5 pb-2 text-[18px] font-semibold leading-7 text-[var(--text-primary)] sticky left-0">
        {{ t('Settings') }}
      </h3>
      <div class="relative flex w-full max-md:pe-3">
        <div
          class="flex-1 flex-shrink-0 flex items-start self-stretch px-3 overflow-auto w-max md:w-full pb-0e border-b border-[var(--border-main)] md:border-b-0 md:flex-col md:gap-3 md:px-2 max-md:gap-[10px]">
          <div class="flex md:gap-[2px] gap-[10px] md:flex-col items-start self-stretch">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="setActiveTab(tab.id)"
              :class="[
                'flex px-1 py-2 items-center text-[14px] leading-5 text-[var(--text-primary)] max-md:whitespace-nowrap md:h-8 md:gap-2 md:self-stretch md:px-4 md:rounded-lg hover:bg-[var(--fill-tsp-white-main)]',
                {
                  'md:bg-[var(--fill-tsp-white-main)] font-medium max-md:border-b-[2px] max-md:border-[var(--Button-primray-black)]': activeTab === tab.id
                }
              ]">
              <span class="hidden md:block" :class="activeTab === tab.id ? 'text-[var(--icon-primary)]' : 'text-[var(--icon-secondary)]'">
                <component :is="tab.icon" class="w-4 h-4" />
              </span>
              <span class="truncate">{{ t(tab.label) }}</span>
            </button>
          </div>
          <div class="hidden md:block self-stretch px-2.5">
            <div class="h-[1px] bg-[var(--border-primary)]"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Content -->
    <div class="flex flex-col items-start self-stretch flex-1 overflow-hidden">
      <div
        class="gap-1 items-center px-6 py-5 hidden md:flex self-stretch border-b border-[var(--border-main)]">
        <!-- Show back button for sub-pages -->
        <ChevronLeft
          v-if="currentSubPage"
          :size="24"
          stroke="var(--icon-tertiary)"
          :stroke-width="2"
          class="clickable hover:opacity-80 cursor-pointer mr-1"
          @click="handleBack" />
        <h3 class="text-[18px] font-semibold leading-7 text-[var(--text-primary)]">
          {{ activeTabTitle }}
        </h3>
      </div>
      <div
        class="flex-1 self-stretch items-start overflow-y-auto flex flex-col gap-[32px] px-4 pt-4 pb-4 md:px-6 md:pt-4">
        <slot :name="currentSlotName" :active-tab="activeTab" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChevronLeft } from 'lucide-vue-next'
import ManusLogoIcon from '@/components/icons/ManusLogoIcon.vue'
import ManusLogoTextIcon from '@/components/icons/ManusLogoTextIcon.vue'

export interface TabItem {
  id: string
  label: string
  icon: any
}

export interface SubPageConfig {
  id: string
  title: string
  parentTabId?: string
}

interface Props {
  tabs: TabItem[]
  defaultTab?: string
  currentSubPage?: string | null
  subPageConfigs?: SubPageConfig[]
}

const props = withDefaults(defineProps<Props>(), {
  defaultTab: undefined,
  currentSubPage: null,
  subPageConfigs: () => []
})

const emit = defineEmits<{
  tabChange: [tabId: string]
  navigateToProfile: []
  back: []
}>()

const { t } = useI18n()

// Active tab state
const activeTab = ref<string>(props.defaultTab || props.tabs[0]?.id || '')

// Computed active tab title
const activeTabTitle = computed(() => {
  // Show sub-page title if in sub-page
  if (props.currentSubPage) {
    const subPageConfig = props.subPageConfigs.find(config => config.id === props.currentSubPage)
    if (subPageConfig) {
      return t(subPageConfig.title)
    }
  }
  
  const currentTab = props.tabs.find(tab => tab.id === activeTab.value)
  return currentTab ? t(currentTab.label) : ''
})

// Computed slot name based on current view
const currentSlotName = computed(() => {
  if (props.currentSubPage) {
    const subPageConfig = props.subPageConfigs.find(config => config.id === props.currentSubPage)
    if (subPageConfig && subPageConfig.parentTabId) {
      return `${subPageConfig.parentTabId}-${props.currentSubPage}`
    }
    return props.currentSubPage
  }
  return activeTab.value
})

// Set active tab
const setActiveTab = (tabId: string) => {
  activeTab.value = tabId
  emit('tabChange', tabId)
}

// Handle back button click
const handleBack = () => {
  emit('back')
}

// Expose active tab for parent component
defineExpose({
  activeTab
})
</script>
