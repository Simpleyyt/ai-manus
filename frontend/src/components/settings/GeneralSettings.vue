<template>
  <div class="space-y-6 w-full">
    <div class="space-y-4">
      <div class="text-[16px] font-medium text-[var(--text-primary)] leading-[22px]">
        {{ t('Appearance') }}
      </div>
      <div class="space-y-6">
        <div class="space-y-2">
          <p>{{ t('Language') }}</p>
          <Select v-model="selectedLanguage" @update:model-value="onLanguageChange">
            <SelectTrigger
              class="w-[208px] h-9 px-3 rounded-lg bg-[var(--fill-tsp-white-light)] border border-[var(--border-white)] hover:bg-[var(--fill-tsp-white-light)]"
            >
              <SelectValue :placeholder="t('Select language')" />
            </SelectTrigger>
            <SelectContent :side-offset="5">
              <SelectItem
                v-for="option in languageOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="space-y-2">
          <p>{{ t('Theme') }}</p>
          <div class="flex items-center gap-[8px]">
            <button
              v-for="opt in themeOptions"
              :key="opt.value"
              type="button"
              :class="[
                'w-[110px] min-h-[32px] rounded-[10px] px-[8px] pt-[12px] pb-[8px] flex flex-col items-center justify-center space-y-[2px] cursor-pointer transition-colors',
                themeMode === opt.value
                  ? 'border-[1.5px] border-[var(--Button-black)] text-[var(--text-primary)]'
                  : 'border border-[var(--Button-border-secondary)] text-[var(--text-secondary)] hover:bg-[var(--fill-tsp-white-light)] hover:active:bg-[var(--fill-tsp-white-main)] hover:text-[var(--text-primary)]',
              ]"
              @click="onThemeChange(opt.value)"
            >
              <component :is="opt.icon" class="size-4" />
              <span class="text-[13px] leading-[18px]">{{ t(opt.label) }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="w-full h-[1px] bg-[var(--border-main)]" />

    <div class="space-y-4">
      <div class="text-[16px] font-medium text-[var(--text-primary)] leading-[22px]">
        {{ t('Communication preferences') }}
      </div>
      <div class="space-y-6">
        <div class="rounded-[12px] p-[12px] -m-[12px] transition-colors duration-200 ease-in-out">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div class="flex flex-col items-start justify-center flex-1 min-w-0">
              <span class="text-sm font-medium text-[var(--text-primary)]">
                {{ t('Browser notifications') }}
              </span>
              <div class="text-[13px] text-[var(--text-tertiary)] leading-[18px] w-full">
                {{ t("Get notified in your browser when there's new progress or a task is completed.") }}
              </div>
            </div>
            <SettingsSwitch
              :checked="browserNotificationsEnabled"
              @checked-change="onNotificationToggle"
            />
          </div>
        </div>

        <div class="rounded-[12px] p-[12px] -m-[12px] transition-colors duration-200 ease-in-out">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div class="flex flex-col items-start justify-center flex-1 min-w-0">
              <span class="text-sm font-medium text-[var(--text-primary)]">
                {{ t('Sound alert') }}
              </span>
              <div class="text-[13px] text-[var(--text-tertiary)] leading-[18px] w-full">
                {{ t('Play a sound once when a task is completed while you are away.') }}
              </div>
            </div>
            <SettingsSwitch
              :checked="soundReminderEnabled"
              @checked-change="setSoundReminder"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, type Component } from 'vue'
import { useI18n } from 'vue-i18n'
import { Sun, Moon, Contrast } from 'lucide-vue-next'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { SelectOption } from '@/types/select'
import { useLocale } from '@/composables/useI18n'
import type { Locale } from '@/locales'
import {
  type ThemeMode,
  readStoredThemeMode,
  setThemeMode,
} from '@/composables/useTheme'
import { useChromePrefs } from '@/composables/useChromePrefs'
import SettingsSwitch from './SettingsSwitch.vue'

const { t } = useI18n()
const { currentLocale, setLocale } = useLocale()
const {
  browserNotificationsEnabled,
  soundReminderEnabled,
  setBrowserNotifications,
  setSoundReminder,
} = useChromePrefs()

const selectedLanguage = ref<Locale>(currentLocale.value)
const themeMode = ref<ThemeMode>(readStoredThemeMode())

const languageOptions: SelectOption[] = [
  { value: 'zh', label: t('Simplified Chinese') },
  { value: 'en', label: t('English') },
]

const themeOptions: { value: ThemeMode; label: string; icon: Component }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'auto', label: 'Auto', icon: Contrast },
]

const onLanguageChange = (value: unknown) => {
  if (value && typeof value === 'string') {
    setLocale(value as Locale)
  }
}

const onThemeChange = (mode: ThemeMode) => {
  themeMode.value = mode
  setThemeMode(mode)
}

const onNotificationToggle = async (enabled: boolean) => {
  await setBrowserNotifications(enabled)
}

onMounted(() => {
  themeMode.value = readStoredThemeMode()
})
</script>
