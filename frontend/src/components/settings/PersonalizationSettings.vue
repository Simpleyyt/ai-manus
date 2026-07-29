<template>
  <div class="space-y-6 w-full">
    <p class="text-[13px] text-[var(--text-tertiary)] leading-[18px]">
      {{ t('Manage your identity information for Manus.') }}
    </p>

    <div class="space-y-2">
      <div class="text-[var(--text-secondary)] text-sm leading-[22px]">
        {{ t('Nickname') }}
      </div>
      <div
        class="group rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 flex items-center gap-[10px] bg-[var(--fill-tsp-white-main)] pt-2 pr-3 pb-2 pl-4 focus-within:ring-[1.5px] focus-within:ring-[var(--border-dark)] w-full sm:w-[300px]"
      >
        <input
          v-model="localFullname"
          maxlength="20"
          class="h-full min-w-1 flex-1 bg-transparent outline-none placeholder:text-[var(--text-disable)]"
          :placeholder="t('Unknown User')"
          @blur="handleSubmit"
          @keyup.enter="handleSubmit"
        >
      </div>
      <p class="text-[13px] text-[var(--text-tertiary)] leading-[18px]">
        {{ t('Manus uses this information to personalize responses.') }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'
import { changeFullname } from '@/api/auth'
import { showSuccessToast, showErrorToast } from '@/utils/toast'

const { t } = useI18n()
const { currentUser, loadCurrentUser } = useAuth()
const localFullname = ref(currentUser.value?.fullname || '')

watch(currentUser, (user) => {
  if (user) localFullname.value = user.fullname || ''
}, { immediate: true })

const handleSubmit = async () => {
  const next = localFullname.value.trim()
  if (!next || next === currentUser.value?.fullname) return
  try {
    await changeFullname({ fullname: next })
    await loadCurrentUser()
    showSuccessToast(t('Full name updated successfully'))
  } catch (error: unknown) {
    localFullname.value = currentUser.value?.fullname || ''
    const err = error as { response?: { data?: { message?: string } }; message?: string }
    showErrorToast(err?.response?.data?.message || err?.message || t('Failed to update full name'))
  }
}
</script>
