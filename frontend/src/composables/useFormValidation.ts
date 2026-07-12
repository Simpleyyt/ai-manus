import { ref, computed } from 'vue'

/** Returns an error message when the field is invalid, undefined otherwise. */
export type FieldValidator = () => string | undefined

/**
 * Shared field-level validation state for forms.
 * Pass a map of field name -> validator; call validateField on input/blur
 * and validateForm before submitting.
 */
export function useFormValidation(validators: Record<string, FieldValidator>) {
  const validationErrors = ref<Record<string, string>>({})

  const validateField = (field: string): boolean => {
    const error = validators[field]?.()
    if (error) {
      validationErrors.value = { ...validationErrors.value, [field]: error }
    } else if (field in validationErrors.value) {
      const rest = { ...validationErrors.value }
      delete rest[field]
      validationErrors.value = rest
    }
    return !error
  }

  const validateForm = (): boolean => {
    let valid = true
    for (const field of Object.keys(validators)) {
      if (!validateField(field)) {
        valid = false
      }
    }
    return valid
  }

  const clearErrors = () => {
    validationErrors.value = {}
  }

  const hasErrors = computed(() => Object.keys(validationErrors.value).length > 0)

  return { validationErrors, validateField, validateForm, clearErrors, hasErrors }
}
