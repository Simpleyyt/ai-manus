<template>
  <AuthFormLayout @submit="handleSubmit">
    <FormField id="fullname" :label="t('Full Name')" v-model="formData.fullname" :error="validationErrors.fullname"
      :placeholder="t('Enter your full name')" :disabled="isLoading"
      @update:model-value="validateField('fullname')" @blur="validateField('fullname')" />

    <FormField id="email" :label="t('Email')" v-model="formData.email" :error="validationErrors.email"
      placeholder="mail@domain.com" type="email" :disabled="isLoading" @update:model-value="validateField('email')"
      @blur="validateField('email')" />

    <PasswordField id="password" :label="t('Password')" v-model="formData.password"
      :error="validationErrors.password" :placeholder="t('Enter password')" :disabled="isLoading"
      @update:model-value="validateField('password')" @blur="validateField('password')" />

    <PasswordField id="confirmPassword" :label="t('Confirm Password')" v-model="formData.confirmPassword"
      :error="validationErrors.confirmPassword" :placeholder="t('Enter password again')" :disabled="isLoading"
      @update:model-value="validateField('confirmPassword')" @blur="validateField('confirmPassword')" />

    <SubmitButton :enabled="isFormValid" :loading="isLoading" :label="t('Register')"
      :loading-label="t('Processing...')" />

    <template #footer>
      <FormFooterLink :text="t('Already have an account?')" :link-text="t('Login')"
        @action="emits('switchToLogin')" />
    </template>
  </AuthFormLayout>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/api'
import { validateUserInput } from '@/utils/auth'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import { useFormValidation } from '@/composables/useFormValidation'
import AuthFormLayout from './AuthFormLayout.vue'
import FormField from './FormField.vue'
import PasswordField from './PasswordField.vue'
import SubmitButton from './SubmitButton.vue'
import FormFooterLink from './FormFooterLink.vue'

const { t } = useI18n()

const emits = defineEmits<{
  success: []
  switchToLogin: []
}>()

const { register, isLoading, authError } = useAuth()

const formData = ref({
  fullname: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const { validationErrors, validateField, validateForm, clearErrors, hasErrors } = useFormValidation({
  fullname: () => validateUserInput({ fullname: formData.value.fullname }).errors.fullname,
  email: () => validateUserInput({ email: formData.value.email }).errors.email,
  password: () => validateUserInput({ password: formData.value.password }).errors.password,
  confirmPassword: () =>
    formData.value.password !== formData.value.confirmPassword ? t('Passwords do not match') : undefined
})

const clearForm = () => {
  formData.value = {
    fullname: '',
    email: '',
    password: '',
    confirmPassword: ''
  }
  clearErrors()
}

const isFormValid = computed(() => {
  const hasRequiredFields = !!(formData.value.fullname.trim() &&
    formData.value.email.trim() &&
    formData.value.password.trim() &&
    formData.value.confirmPassword.trim())
  return hasRequiredFields && !hasErrors.value
})

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  try {
    await register({
      fullname: formData.value.fullname,
      email: formData.value.email,
      password: formData.value.password
    })

    showSuccessToast(t('Registration successful! Welcome to Manus'))
    emits('success')
  } catch (error) {
    console.error('Registration failed:', error)
    showErrorToast(authError.value || t('Registration failed, please try again'))
  }
}

// Re-validate confirm password when original password changes
watch(() => formData.value.password, () => {
  if (formData.value.confirmPassword) {
    validateField('confirmPassword')
  }
})

// Expose clearForm method for parent component
defineExpose({
  clearForm
})
</script>
