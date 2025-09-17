<template>
  <div class="w-full max-w-[384px] py-[24px] pt-0 px-[12px] relative" style="z-index:1">
    <div class="flex flex-col justify-center gap-[40px] text-[var(--text-primary)] max-sm:gap-[12px]">
      <form @submit.prevent="handleSubmit" class="flex flex-col items-stretch gap-[20px]">
        <div class="relative">
          <div class="transition-all duration-500 ease-out opacity-100 scale-100">
            <div class="flex flex-col gap-[12px]">

              <!-- Verification code field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="verifyCode"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Verification code sent to') }}<b>{{ props.email }}</b></span>
                  </label>
                </div>
                <div class="w-full relative">
                  <input v-model="formData.verificationCode"
                    class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 w-full disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] pr-[128px]"
                    :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.verificationCode }"
                    :placeholder="t('Enter 6-digit verification code')" id="verifyCode" type="text" maxlength="6" pattern="[0-9]{6}"
                    inputmode="numeric"
                    :disabled="isLoading"
                    @input="handleVerificationCodeInput" 
                    @blur="validateField('verificationCode')"
                    @paste="handlePaste">
                  <!-- Resend button or countdown -->
                  <div
                    class="absolute w-[120px] z-[30] top-1/2 right-0 -translate-y-1/2 text-center border-l-[1px] border-l-color-[var(--border-main)] leading-[0px]">
                    <!-- Show resend button when countdown is 0 -->
                    <div v-if="resendCooldown === 0"
                      class="inline-flex min-w-[60px] justify-center items-center gap-[4px] text-[var(--text-blue)] text-[14px] font-[400] tracking-[0px] leading-[22px] select-none flex-1 cursor-pointer hover:opacity-80 active:opacity-70 duration-150"
                      @click="handleResendCode">
                      {{ t('Resend') }}
                    </div>
                    <!-- Show countdown when resending is on cooldown -->
                    <span v-else
                      class="inline-block min-w-[60px] text-[var(--text-blue)] text-center text-[14px] leading-[18px] select-none opacity-50 transition-opacity">
                      {{ resendCooldown }}s
                    </span>
                  </div>
                </div>
                <!-- Error message for verification code -->
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.verificationCode ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.verificationCode }}
                </div>
              </div>

              <!-- New password field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="new-password"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('New Password') }}</span>
                  </label>
                </div>
                <div class="relative w-full">
                  <input v-model="formData.newPassword"
                    class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pr-10 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] w-full"
                    :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.newPassword }" id="new-password"
                    :placeholder="t('Enter your new password')" :type="showNewPassword ? 'text' : 'password'"
                    :disabled="isLoading" @input="validateField('newPassword')" @blur="validateField('newPassword')">
                  <button type="button" @click="showNewPassword = !showNewPassword"
                    class="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] transition-colors">
                    <Eye v-if="showNewPassword" :size="16" />
                    <EyeOff v-else :size="16" />
                  </button>
                </div>
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.newPassword ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.newPassword }}
                </div>
              </div>

              <!-- Confirm password field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="confirm-password"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Confirm Password') }}</span>
                  </label>
                </div>
                <div class="relative w-full">
                  <input v-model="formData.confirmPassword"
                    class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pr-10 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] w-full"
                    :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.confirmPassword }"
                    id="confirm-password" :placeholder="t('Confirm your new password')"
                    :type="showConfirmPassword ? 'text' : 'password'" :disabled="isLoading"
                    @input="validateField('confirmPassword')" @blur="validateField('confirmPassword')">
                  <button type="button" @click="showConfirmPassword = !showConfirmPassword"
                    class="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] transition-colors">
                    <Eye v-if="showConfirmPassword" :size="16" />
                    <EyeOff v-else :size="16" />
                  </button>
                </div>
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.confirmPassword ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.confirmPassword }}
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
                <span>{{ isLoading ? t('Updating...') : t('Update Password') }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div
          class="flex flex-col gap-[8px] text-center text-[13px] leading-[18px] text-[var(--text-tertiary)] mt-[8px]">

          <!-- Back to login -->
          <div>
            <span>{{ isPasswordUpdated ? t('Ready to login?') : t('Want to try a different email?') }}</span>
            <span
              class="ms-[8px] text-[var(--text-secondary)] cursor-pointer select-none hover:opacity-80 active:opacity-70 transition-all underline"
              @click="handleBackAction">
              {{ isPasswordUpdated ? t('Back to Login') : t('Go Back') }}
            </span>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { LoaderCircle, Eye, EyeOff } from 'lucide-vue-next'
import { validateUserInput } from '@/utils/auth'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import { sendVerificationCode, resetPassword } from '@/api/auth'

const { t } = useI18n()

// Props
interface Props {
  email: string
}

const props = defineProps<Props>()

// Emits
const emits = defineEmits<{
  success: []
  backToEmail: []
  backToLogin: []
}>()

// Form state
const isLoading = ref(false)
const isPasswordUpdated = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

// Resend cooldown
const resendCooldown = ref(0)
let resendTimer: number | null = null

// Form data
const formData = ref({
  verificationCode: '',
  newPassword: '',
  confirmPassword: ''
})

// Format verification code input (only allow digits)
const formatVerificationCode = (value: string) => {
  return value.replace(/\D/g, '').slice(0, 6)
}

// Handle verification code input
const handleVerificationCodeInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const formatted = formatVerificationCode(target.value)
  formData.value.verificationCode = formatted
  validateField('verificationCode')
}

// Handle paste event for verification code
const handlePaste = (event: ClipboardEvent) => {
  event.preventDefault()
  const paste = event.clipboardData?.getData('text') || ''
  formData.value.verificationCode = formatVerificationCode(paste)
  validateField('verificationCode')
}

// Validation errors
const validationErrors = ref<Record<string, string>>({})

// Clear form
const clearForm = () => {
  formData.value = {
    verificationCode: '',
    newPassword: '',
    confirmPassword: ''
  }
  validationErrors.value = {}
  isPasswordUpdated.value = false
  showNewPassword.value = false
  showConfirmPassword.value = false
}

// Validate single field
const validateField = (field: string) => {
  const errors: Record<string, string> = {}

  if (field === 'verificationCode') {
    if (!formData.value.verificationCode.trim()) {
      errors.verificationCode = t('Verification code is required')
    } else if (!/^\d{6}$/.test(formData.value.verificationCode.trim())) {
      errors.verificationCode = t('Verification code must be 6 digits')
    }
  }

  if (field === 'newPassword') {
    const result = validateUserInput({ password: formData.value.newPassword })
    if (result.errors.password) {
      errors.newPassword = result.errors.password
    }
  }

  if (field === 'confirmPassword') {
    if (!formData.value.confirmPassword.trim()) {
      errors.confirmPassword = t('Please confirm your password')
    } else if (formData.value.newPassword !== formData.value.confirmPassword) {
      errors.confirmPassword = t('Passwords do not match')
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
  // Validate all fields
  validateField('verificationCode')
  validateField('newPassword')
  validateField('confirmPassword')

  return Object.keys(validationErrors.value).length === 0
}

// Check if form is valid
const isFormValid = computed(() => {
  const hasRequiredFields = formData.value.verificationCode.trim() &&
    formData.value.newPassword.trim() &&
    formData.value.confirmPassword.trim()
  const hasNoErrors = Object.keys(validationErrors.value).length === 0
  return hasRequiredFields && hasNoErrors && !isPasswordUpdated.value
})

// Start resend cooldown
const startResendCooldown = () => {
  resendCooldown.value = 60
  resendTimer = setInterval(() => {
    resendCooldown.value--
    if (resendCooldown.value <= 0) {
      clearInterval(resendTimer!)
      resendTimer = null
    }
  }, 1000)
}

// Handle resend verification code
const handleResendCode = async () => {
  if (resendCooldown.value > 0) return

    // Call the real API to send verification code
    sendVerificationCode({ email: props.email }).then(() => {
      showSuccessToast(t('Verification code sent again'))
      console.log('Resend verification code to:', props.email)
    }).catch((error: any) => {
      console.error('Resend verification code failed:', error)
      showErrorToast(t('Failed to resend verification code. Please try again.') + ': ' + error.response?.data?.message || error.message || 'Unknown error')
    })
    startResendCooldown()
}

// Submit form
const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  isLoading.value = true

  try {
    // Call the real API to reset password
    await resetPassword({
      email: props.email,
      verification_code: formData.value.verificationCode,
      new_password: formData.value.newPassword
    })

    // Show success state
    isPasswordUpdated.value = true
    showSuccessToast(t('Password updated successfully'))

    console.log('Password reset completed for:', props.email)

    // Auto redirect to login after 3 seconds
    setTimeout(() => {
      if (isPasswordUpdated.value) {
        emits('success')
      }
    }, 500)

  } catch (error: any) {
    console.error('Password reset verification failed:', error)
    const errorMessage = error.response?.data?.message || error.message || 'Unknown error'
    
    // Handle specific error cases
    if (error.response?.status === 401) {
      showErrorToast(t('Invalid or expired verification code. Please try again.'))
    } else if (error.response?.status === 404) {
      showErrorToast(t('User not found. Please check your email address.'))
    } else if (error.response?.status === 400) {
      showErrorToast(t('Invalid request. Please check your input and try again.'))
    } else {
      showErrorToast(t('Failed to update password. Please try again.') + ': ' + errorMessage)
    }
  } finally {
    isLoading.value = false
  }
}

// Handle back actions
const handleBackAction = () => {
  if (isPasswordUpdated.value) {
    emits('backToLogin')
  } else {
    emits('backToEmail')
  }
}

// Send initial verification code and start resend cooldown on mount
onMounted(async () => {
  // Start cooldown timer
  startResendCooldown()
})

// Cleanup timer on unmount
onUnmounted(() => {
  if (resendTimer) {
    clearInterval(resendTimer)
    resendTimer = null
  }
})

// Expose methods for parent component
defineExpose({
  clearForm
})
</script>
