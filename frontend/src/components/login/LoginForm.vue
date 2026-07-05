<template>
  <AuthFormLayout @submit="handleSubmit">
    <FormField id="email" :label="t('Email')" v-model="formData.email" :error="validationErrors.email"
      placeholder="mail@domain.com" type="email" :disabled="isLoading" @update:model-value="validateField('email')"
      @blur="validateField('email')" />

    <PasswordField id="password" :label="t('Password')" v-model="formData.password"
      :error="validationErrors.password" :placeholder="t('Enter password')" :disabled="isLoading"
      @update:model-value="validateField('password')" @blur="validateField('password')">
      <template #label-extra>
        <span
          class="underline text-[var(--text-tertiary)] text-[13px] leading-[18px] transition-opacity cursor-pointer select-none hover:opacity-80 active:opacity-80"
          @click="emits('switchToReset')">{{ t('Forgot Password?') }}</span>
      </template>
    </PasswordField>

    <SubmitButton :enabled="isFormValid" :loading="isLoading" :label="t('Login')" :loading-label="t('Processing...')" />

    <template #footer>
      <FormFooterLink v-if="hasRegister" :text="t('Don\'t have an account?')" :link-text="t('Register')"
        @action="emits('switchToRegister')" />
    </template>
  </AuthFormLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/api'
import { validateUserInput } from '@/utils/auth'
import { showErrorToast, showSuccessToast } from '@/utils/toast'
import { getCachedAuthProvider } from '@/api/config'
import { useFormValidation } from '@/composables/useFormValidation'
import AuthFormLayout from './AuthFormLayout.vue'
import FormField from './FormField.vue'
import PasswordField from './PasswordField.vue'
import SubmitButton from './SubmitButton.vue'
import FormFooterLink from './FormFooterLink.vue'

const { t } = useI18n()

const emits = defineEmits<{
  success: []
  switchToRegister: []
  switchToReset: []
}>()

const { login, isLoading, authError } = useAuth()
const hasRegister = ref(false)

const formData = ref({
  email: '',
  password: ''
})

const { validationErrors, validateField, validateForm, clearErrors, hasErrors } = useFormValidation({
  email: () => validateUserInput({ email: formData.value.email }).errors.email,
  password: () => validateUserInput({ password: formData.value.password }).errors.password
})

const clearForm = () => {
  formData.value = {
    email: '',
    password: ''
  }
  clearErrors()
}

const isFormValid = computed(() => {
  const hasRequiredFields = !!(formData.value.email.trim() && formData.value.password.trim())
  return hasRequiredFields && !hasErrors.value
})

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  try {
    await login({
      email: formData.value.email,
      password: formData.value.password
    })

    showSuccessToast(t('Login successful! Welcome back'))
    emits('success')
  } catch (error) {
    console.error('Login failed:', error)
    showErrorToast(authError.value || t('Login failed, please try again'))
  }
}

onMounted(async () => {
  const authProvider = await getCachedAuthProvider()
  hasRegister.value = authProvider === 'password'
})

// Expose clearForm method for parent component
defineExpose({
  clearForm
})
</script>
