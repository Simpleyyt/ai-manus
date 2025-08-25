<template>
  <div
    class="pb-[32px] last:pb-0 border-b border-[var(--border-light)] last-of-type:border-transparent w-full">
    <div class="text-[13px] font-medium text-[var(--text-tertiary)] mb-1 w-full">{{ t('General') }}</div>
    <div class="mb-[24px] last:mb-[0] w-full">
      <div class="text-sm font-medium text-[var(--text-primary)] mb-[12px]">{{ t('Language') }}</div>
      <Select v-model="selectedLanguage" @update:modelValue="onLanguageChange">
        <SelectTrigger class="w-[208px] h-[36px]">
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
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
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

// Use i18n for translations
const { t } = useI18n()

// Use the project's i18n composable
const { currentLocale, setLocale } = useLocale()

// Language selection
const selectedLanguage = ref<Locale>(currentLocale.value)

const languageOptions: SelectOption[] = [
  { value: 'zh', label: t('Simplified Chinese') },
  { value: 'en', label: t('English') },
]

const onLanguageChange = (value: any) => {
  if (value && typeof value === 'string') {
    const locale = value as Locale
    setLocale(locale)
    console.log('Language changed to:', locale)
  }
}
</script>
