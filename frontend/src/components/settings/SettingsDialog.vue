<template>
  <Dialog v-model:open="isSettingsDialogOpen">
    <DialogContent class="w-[380px] md:w-[95vw] md:max-w-[920px]">
      <DialogTitle></DialogTitle>
      <DialogDescription></DialogDescription>
      
      <SettingsTabs 
        :tabs="tabs" 
        :default-tab="defaultTab"
        :current-sub-page="currentSubPage"
        :sub-page-configs="subPageConfigs"
        @tab-change="onTabChange"
        @navigate-to-profile="navigateToProfile"
        @back="goBack">
        
        <template #account>
          <AccountSettings @navigate-to-profile="navigateToProfile" />
        </template>
        
        <template #account-profile>
          <ProfileSettings @back="goBack" />
        </template>
        
        <template #settings>
          <GeneralSettings />
        </template>
        
      </SettingsTabs>
      
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { UserRound, Settings2 } from 'lucide-vue-next'
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { useSettingsDialog } from '@/composables/useSettingsDialog'
import SettingsTabs from './SettingsTabs.vue'
import AccountSettings from './AccountSettings.vue'
import GeneralSettings from './GeneralSettings.vue'
import ProfileSettings from './ProfileSettings.vue'
import type { TabItem, SubPageConfig } from './SettingsTabs.vue'

// Use global settings dialog state
const { isSettingsDialogOpen, defaultTab } = useSettingsDialog()

// Navigation state for sub-pages
const currentSubPage = ref<string | null>(null)

// Tab configuration
const tabs: TabItem[] = [
  {
    id: 'account',
    label: 'Account',
    icon: UserRound
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings2
  }
]

// Sub-page configuration
const subPageConfigs: SubPageConfig[] = [
  {
    id: 'profile',
    title: 'Profile',
    parentTabId: 'account'
  }
]

// Handle tab change
const onTabChange = (_tabId: string) => {
  // Reset sub-page when changing tabs
  currentSubPage.value = null
}

// Navigate to profile sub-page
const navigateToProfile = () => {
  currentSubPage.value = 'profile'
}

// Go back to main view
const goBack = () => {
  currentSubPage.value = null
}
</script>