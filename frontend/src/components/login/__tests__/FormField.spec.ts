import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FormField from '../FormField.vue'
import PasswordField from '../PasswordField.vue'
import SubmitButton from '../SubmitButton.vue'

describe('FormField', () => {
  it('renders label and forwards input events', async () => {
    const wrapper = mount(FormField, {
      props: { id: 'email', label: 'Email', modelValue: '' }
    })
    expect(wrapper.find('label').text()).toBe('Email')

    await wrapper.find('input').setValue('a@b.com')
    expect(wrapper.emitted('update:modelValue')).toEqual([['a@b.com']])
  })

  it('shows the error message and error styling when error is set', async () => {
    const wrapper = mount(FormField, {
      props: { id: 'email', label: 'Email', modelValue: '', error: 'Required' }
    })
    expect(wrapper.text()).toContain('Required')
    expect(wrapper.find('input').classes().join(' ')).toContain('ring-[var(--function-error)]')
  })

  it('hides the error block when there is no error', () => {
    const wrapper = mount(FormField, {
      props: { id: 'email', label: 'Email', modelValue: '' }
    })
    const divs = wrapper.findAll('div')
    const errorBlock = divs[divs.length - 1]
    expect(errorBlock.classes()).toContain('opacity-0')
  })
})

describe('PasswordField', () => {
  it('toggles between password and text input types', async () => {
    const wrapper = mount(PasswordField, {
      props: { id: 'password', label: 'Password', modelValue: 'secret' }
    })
    const input = wrapper.find('input')
    expect(input.attributes('type')).toBe('password')

    await wrapper.find('button').trigger('click')
    expect(input.attributes('type')).toBe('text')

    await wrapper.find('button').trigger('click')
    expect(input.attributes('type')).toBe('password')
  })

  it('emits update:modelValue on input', async () => {
    const wrapper = mount(PasswordField, {
      props: { id: 'password', label: 'Password', modelValue: '' }
    })
    await wrapper.find('input').setValue('hunter2')
    expect(wrapper.emitted('update:modelValue')).toEqual([['hunter2']])
  })
})

describe('SubmitButton', () => {
  it('is disabled and shows the loading label while loading', () => {
    const wrapper = mount(SubmitButton, {
      props: { enabled: true, loading: true, label: 'Login', loadingLabel: 'Processing...' }
    })
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Processing...')
  })

  it('is enabled and shows the label when idle and valid', () => {
    const wrapper = mount(SubmitButton, {
      props: { enabled: true, loading: false, label: 'Login', loadingLabel: 'Processing...' }
    })
    expect(wrapper.find('button').attributes('disabled')).toBeUndefined()
    expect(wrapper.text()).toContain('Login')
  })

  it('is disabled when the form is invalid', () => {
    const wrapper = mount(SubmitButton, {
      props: { enabled: false, loading: false, label: 'Login', loadingLabel: 'Processing...' }
    })
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })
})
