<template>
  <div class="w-full max-w-[384px] relative z-[1]">
    <!-- Step 1: Email input for sending verification code -->
    <AuthFormLayout v-if="currentStep === 'email'" @submit="handleSendCode">
      <FormField id="reset-email" :label="t('Email')" v-model="formData.email" :error="validationErrors.email"
        placeholder="mail@domain.com" type="email" :disabled="isLoading" @update:model-value="validateField('email')"
        @blur="validateField('email')" />

      <SubmitButton :enabled="isFormValid" :loading="isLoading" :label="t('Send Verification Code')"
        :loading-label="t('Sending Code...')" />

      <template #footer>
        <FormFooterLink :text="t('Remember your password?')" :link-text="t('Back to Login')"
          @action="emits('backToLogin')" />
      </template>
    </AuthFormLayout>

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
import { validateUserInput } from '@/utils/auth'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import { sendVerificationCode } from '@/api/auth'
import { useFormValidation } from '@/composables/useFormValidation'
import AuthFormLayout from './AuthFormLayout.vue'
import FormField from './FormField.vue'
import SubmitButton from './SubmitButton.vue'
import FormFooterLink from './FormFooterLink.vue'
import ResetPasswordVerificationForm from './ResetPasswordVerificationForm.vue'

const { t } = useI18n()

const emits = defineEmits<{
  backToLogin: []
}>()

const isLoading = ref(false)
const currentStep = ref<'email' | 'verification'>('email')

const formData = ref({
  email: ''
})

const { validationErrors, validateField, validateForm, clearErrors, hasErrors } = useFormValidation({
  email: () => validateUserInput({ email: formData.value.email }).errors.email
})

const clearForm = () => {
  formData.value = {
    email: ''
  }
  clearErrors()
  currentStep.value = 'email'
}

const isFormValid = computed(() => {
  return !!formData.value.email.trim() && !hasErrors.value
})

const handleSendCode = async () => {
  if (!validateForm()) {
    return
  }

  isLoading.value = true

  try {
    await sendVerificationCode({ email: formData.value.email })

    // Switch to verification step
    currentStep.value = 'verification'
    showSuccessToast(t('Verification code sent to your email'))
  } catch (error) {
    console.error('Send verification code failed:', error)
    showErrorToast(t('Failed to send verification code. Please try again.'))
  } finally {
    isLoading.value = false
  }
}

// Handle successful password reset
const handleResetSuccess = () => {
  clearForm()
  emits('backToLogin')
}

const backToEmailStep = () => {
  currentStep.value = 'email'
  clearErrors()
}

// Expose methods for parent component
defineExpose({
  clearForm
})
</script>
