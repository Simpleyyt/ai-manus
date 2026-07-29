<template>
  <Dialog v-model:open="isSettingsDialogOpen">
    <DialogContent
      class="w-[380px] max-w-[98%] md:w-[80vw] md:min-w-[720px] md:max-w-[1440px] min-h-[400px] overflow-hidden rounded-[16px] border-0 shadow-menu"
    >
      <DialogTitle class="sr-only">{{ t('Settings') }}</DialogTitle>
      <DialogDescription class="sr-only">{{ t('Settings') }}</DialogDescription>

      <SettingsTabs :default-tab="defaultTab" @tab-change="onTabChange">
        <template #general>
          <GeneralSettings />
        </template>
        <template #account>
          <AccountSettings />
        </template>
        <template #shortcuts>
          <ShortcutsSettings />
        </template>
        <template #personalization>
          <PersonalizationSettings />
        </template>
        <template #help>
          <HelpSettings />
        </template>
      </SettingsTabs>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { useSettingsDialog } from '@/composables/useSettingsDialog'
import SettingsTabs from './SettingsTabs.vue'
import GeneralSettings from './GeneralSettings.vue'
import AccountSettings from './AccountSettings.vue'
import ShortcutsSettings from './ShortcutsSettings.vue'
import PersonalizationSettings from './PersonalizationSettings.vue'
import HelpSettings from './HelpSettings.vue'

const { t } = useI18n()
const { isSettingsDialogOpen, defaultTab } = useSettingsDialog()

const onTabChange = (_tabId: string) => {
  /* tab state owned by SettingsTabs */
}
</script>
