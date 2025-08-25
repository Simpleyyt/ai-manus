<template>
  <div class="w-full max-w-[384px] py-[24px] pt-0 px-[12px] relative" style="z-index:1">
    <!-- Step 1: Email input for sending verification code -->
    <div v-if="currentStep === 'email'" class="flex flex-col justify-center gap-[40px] text-[var(--text-primary)] max-sm:gap-[12px]">
      <form @submit.prevent="handleSendCode" class="flex flex-col items-stretch gap-[20px]">
        <div class="relative">
          <div class="transition-all duration-500 ease-out opacity-100 scale-100">
            <div class="flex flex-col gap-[12px]">

              <!-- Email field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="reset-email"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Email') }}</span>
                  </label>
                </div>
                <input v-model="formData.email"
                  class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pr-1.5 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] w-full"
                  :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.email }" id="reset-email"
                  placeholder="mail@domain.com" type="email" :disabled="isLoading" @input="validateField('email')"
                  @blur="validateField('email')">
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.email ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.email }}
                </div>
              </div>

              <!-- Submit button -->
              <button type="submit"
                class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors h-[40px] px-[16px] rounded-[10px] gap-[6px] text-sm min-w-16 w-full"
                :class="isFormValid && !isLoading
                  ? 'bg-[var(--Button-primary-black)] text-[var(--text-onblack)] hover:opacity-90 active:opacity-80'
                  : 'bg-[#898988] dark:bg-[#939393] text-[var(--text-onblack)] opacity-50 cursor-not-allowed'"
                :disabled="!isFormValid || isLoading">
                <LoaderCircle v-if="isLoading" :size="16" class="animate-spin" />
                <span>{{ isLoading ? t('Sending Code...') : t('Send Verification Code') }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Back to login -->
        <div class="text-center text-[13px] leading-[18px] text-[var(--text-tertiary)] mt-[8px]">
          <span>{{ t('Remember your password?') }}</span>
          <span
            class="ms-[8px] text-[var(--text-secondary)] cursor-pointer select-none hover:opacity-80 active:opacity-70 transition-all underline"
            @click="emits('backToLogin')">
            {{ t('Back to Login') }}
          </span>
        </div>
      </form>
    </div>

    <!-- Step 2: Verification code and password reset -->
    <ResetPasswordVerificationForm 
      v-else-if="currentStep === 'verification'"
      :email="formData.email"
      @success="handleResetSuccess"
      @back-to-email="backToEmailStep"
      @back-to-login="emits('backToLogin')" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { LoaderCircle } from 'lucide-vue-next'
import { validateUserInput } from '@/utils/auth'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import { sendVerificationCode } from '@/api/auth'
import ResetPasswordVerificationForm from './ResetPasswordVerificationForm.vue'

const { t } = useI18n()

// Emits
const emits = defineEmits<{
  backToLogin: []
}>()

// Form state
const isLoading = ref(false)
const currentStep = ref<'email' | 'verification'>('email')

// Form data
const formData = ref({
  email: ''
})

// Validation errors
const validationErrors = ref<Record<string, string>>({})

// Clear form
const clearForm = () => {
  formData.value = {
    email: ''
  }
  validationErrors.value = {}
  currentStep.value = 'email'
}

// Validate single field
const validateField = (field: string) => {
  const errors: Record<string, string> = {}

  if (field === 'email') {
    const result = validateUserInput({ email: formData.value.email })
    if (result.errors.email) {
      errors.email = result.errors.email
    }
  }

  // Update error state
  Object.keys(errors).forEach(key => {
    validationErrors.value[key] = errors[key]
  })

  // Clear fixed errors
  if (!errors[field]) {
    delete validationErrors.value[field]
  }
}

// Validate entire form
const validateForm = () => {
  const data = {
    email: formData.value.email
  }

  const result = validateUserInput(data)
  validationErrors.value = { ...result.errors }

  return Object.keys(validationErrors.value).length === 0
}

// Check if form is valid
const isFormValid = computed(() => {
  const hasRequiredFields = formData.value.email.trim()
  const hasNoErrors = Object.keys(validationErrors.value).length === 0
  return hasRequiredFields && hasNoErrors
})

// Send verification code
const handleSendCode = async () => {
  if (!validateForm()) {
    return
  }

  isLoading.value = true

  try {
    // Call the API to send verification code
    await sendVerificationCode({ email: formData.value.email })
    
    // Switch to verification step
    currentStep.value = 'verification'
    showSuccessToast(t('Verification code sent to your email'))
    
    console.log('Verification code sent to:', formData.value.email)
  } catch (error: any) {
    console.error('Send verification code failed:', error)
    showErrorToast(t('Failed to send verification code. Please try again.'))
  } finally {
    isLoading.value = false
  }
}

// Handle successful password reset
const handleResetSuccess = () => {
  // Reset form and go back to login
  clearForm()
  emits('backToLogin')
}

// Go back to email step
const backToEmailStep = () => {
  currentStep.value = 'email'
  validationErrors.value = {}
}

// Expose methods for parent component
defineExpose({
  clearForm
})
</script>
