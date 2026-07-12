<template>
  <AuthFormLayout @submit="handleSubmit">
    <!-- Verification code field -->
    <FormField id="verifyCode" :error="validationErrors.verificationCode">
      <template #label>
        <span>{{ t('Verification code sent to') }}<b>{{ props.email }}</b></span>
      </template>
      <div class="w-full relative">
        <input v-model="formData.verificationCode"
          class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 w-full disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] pr-[128px]"
          :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.verificationCode }"
          :placeholder="t('Enter 6-digit verification code')" id="verifyCode" type="text" maxlength="6"
          pattern="[0-9]{6}" inputmode="numeric" :disabled="isLoading" @input="handleVerificationCodeInput"
          @blur="validateField('verificationCode')" @paste="handlePaste">
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
    </FormField>

    <PasswordField id="new-password" :label="t('New Password')" v-model="formData.newPassword"
      :error="validationErrors.newPassword" :placeholder="t('Enter your new password')" :disabled="isLoading"
      @update:model-value="validateField('newPassword')" @blur="validateField('newPassword')" />

    <PasswordField id="confirm-password" :label="t('Confirm Password')" v-model="formData.confirmPassword"
      :error="validationErrors.confirmPassword" :placeholder="t('Confirm your new password')" :disabled="isLoading"
      @update:model-value="validateField('confirmPassword')" @blur="validateField('confirmPassword')" />

    <SubmitButton :enabled="isFormValid" :loading="isLoading" :label="t('Update Password')"
      :loading-label="t('Updating...')" />

    <template #footer>
      <FormFooterLink :text="isPasswordUpdated ? t('Ready to login?') : t('Want to try a different email?')"
        :link-text="isPasswordUpdated ? t('Back to Login') : t('Go Back')" @action="handleBackAction" />
    </template>
  </AuthFormLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { validateUserInput } from '@/utils/auth'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import { sendVerificationCode, resetPassword } from '@/api/auth'
import { useFormValidation } from '@/composables/useFormValidation'
import AuthFormLayout from './AuthFormLayout.vue'
import FormField from './FormField.vue'
import PasswordField from './PasswordField.vue'
import SubmitButton from './SubmitButton.vue'
import FormFooterLink from './FormFooterLink.vue'

const { t } = useI18n()

const props = defineProps<{
  email: string
}>()

const emits = defineEmits<{
  success: []
  backToEmail: []
  backToLogin: []
}>()

const isLoading = ref(false)
const isPasswordUpdated = ref(false)

// Resend cooldown
const resendCooldown = ref(0)
let resendTimer: number | null = null

const formData = ref({
  verificationCode: '',
  newPassword: '',
  confirmPassword: ''
})

// Format verification code input (only allow digits)
const formatVerificationCode = (value: string) => {
  return value.replace(/\D/g, '').slice(0, 6)
}

const handleVerificationCodeInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  formData.value.verificationCode = formatVerificationCode(target.value)
  validateField('verificationCode')
}

const handlePaste = (event: ClipboardEvent) => {
  event.preventDefault()
  const paste = event.clipboardData?.getData('text') || ''
  formData.value.verificationCode = formatVerificationCode(paste)
  validateField('verificationCode')
}

const { validationErrors, validateField, validateForm, clearErrors, hasErrors } = useFormValidation({
  verificationCode: () => {
    if (!formData.value.verificationCode.trim()) {
      return t('Verification code is required')
    }
    if (!/^\d{6}$/.test(formData.value.verificationCode.trim())) {
      return t('Verification code must be 6 digits')
    }
    return undefined
  },
  newPassword: () => validateUserInput({ password: formData.value.newPassword }).errors.password,
  confirmPassword: () => {
    if (!formData.value.confirmPassword.trim()) {
      return t('Please confirm your password')
    }
    if (formData.value.newPassword !== formData.value.confirmPassword) {
      return t('Passwords do not match')
    }
    return undefined
  }
})

const clearForm = () => {
  formData.value = {
    verificationCode: '',
    newPassword: '',
    confirmPassword: ''
  }
  clearErrors()
  isPasswordUpdated.value = false
}

const isFormValid = computed(() => {
  const hasRequiredFields = !!(formData.value.verificationCode.trim() &&
    formData.value.newPassword.trim() &&
    formData.value.confirmPassword.trim())
  return hasRequiredFields && !hasErrors.value && !isPasswordUpdated.value
})

const startResendCooldown = () => {
  resendCooldown.value = 60
  resendTimer = window.setInterval(() => {
    resendCooldown.value--
    if (resendCooldown.value <= 0) {
      clearInterval(resendTimer!)
      resendTimer = null
    }
  }, 1000)
}

const handleResendCode = async () => {
  if (resendCooldown.value > 0) return

  sendVerificationCode({ email: props.email }).then(() => {
    showSuccessToast(t('Verification code sent again'))
  }).catch((error) => {
    console.error('Resend verification code failed:', error)
    showErrorToast(t('Failed to resend verification code. Please try again.') + ': ' + (error.response?.data?.message || error.message || 'Unknown error'))
  })
  startResendCooldown()
}

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  isLoading.value = true

  try {
    await resetPassword({
      email: props.email,
      verification_code: formData.value.verificationCode,
      new_password: formData.value.newPassword
    })

    isPasswordUpdated.value = true
    showSuccessToast(t('Password updated successfully'))

    // Auto redirect to login shortly after success
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

const handleBackAction = () => {
  if (isPasswordUpdated.value) {
    emits('backToLogin')
  } else {
    emits('backToEmail')
  }
}

// The initial verification code is sent by the parent form; only start the cooldown here
onMounted(() => {
  startResendCooldown()
})

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
