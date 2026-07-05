import { describe, it, expect } from 'vitest'
import { useFormValidation } from '../useFormValidation'

describe('useFormValidation', () => {
  const setup = (values: { email?: string; password?: string } = {}) => {
    const state = { email: values.email ?? '', password: values.password ?? '' }
    const form = useFormValidation({
      email: () => (state.email.includes('@') ? undefined : 'invalid email'),
      password: () => (state.password.length >= 6 ? undefined : 'password too short')
    })
    return { state, form }
  }

  it('starts without errors', () => {
    const { form } = setup()
    expect(form.hasErrors.value).toBe(false)
    expect(form.validationErrors.value).toEqual({})
  })

  it('validateField records an error for an invalid field', () => {
    const { form } = setup({ email: 'not-an-email' })
    expect(form.validateField('email')).toBe(false)
    expect(form.validationErrors.value.email).toBe('invalid email')
    expect(form.hasErrors.value).toBe(true)
  })

  it('validateField clears the error once the field becomes valid', () => {
    const { state, form } = setup({ email: 'bad' })
    form.validateField('email')
    expect(form.validationErrors.value.email).toBeDefined()

    state.email = 'good@example.com'
    expect(form.validateField('email')).toBe(true)
    expect(form.validationErrors.value.email).toBeUndefined()
    expect(form.hasErrors.value).toBe(false)
  })

  it('validateField ignores unknown fields', () => {
    const { form } = setup()
    expect(form.validateField('unknown')).toBe(true)
    expect(form.validationErrors.value).toEqual({})
  })

  it('validateForm validates all fields at once', () => {
    const { form } = setup({ email: 'bad', password: '123' })
    expect(form.validateForm()).toBe(false)
    expect(Object.keys(form.validationErrors.value).sort()).toEqual(['email', 'password'])
  })

  it('validateForm returns true when everything is valid', () => {
    const { form } = setup({ email: 'a@b.com', password: 'secret123' })
    expect(form.validateForm()).toBe(true)
    expect(form.hasErrors.value).toBe(false)
  })

  it('clearErrors removes all recorded errors', () => {
    const { form } = setup({ email: 'bad', password: '1' })
    form.validateForm()
    expect(form.hasErrors.value).toBe(true)

    form.clearErrors()
    expect(form.validationErrors.value).toEqual({})
    expect(form.hasErrors.value).toBe(false)
  })
})
