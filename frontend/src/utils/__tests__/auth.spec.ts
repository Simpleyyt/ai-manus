import { describe, it, expect } from 'vitest'
import { validateUserInput, getUserDisplayName, getUserAvatar } from '../auth'
import type { User } from '../../api/auth'

describe('validateUserInput', () => {
  it('accepts valid input', () => {
    const result = validateUserInput({
      fullname: 'Alice Doe',
      email: 'alice@example.com',
      password: 'secret123'
    })
    expect(result.isValid).toBe(true)
    expect(result.errors).toEqual({})
  })

  it('rejects an invalid email', () => {
    const result = validateUserInput({ email: 'not-an-email' })
    expect(result.isValid).toBe(false)
    expect(result.errors.email).toBeTruthy()
  })

  it('rejects a too-short password', () => {
    const result = validateUserInput({ password: '12345' })
    expect(result.isValid).toBe(false)
    expect(result.errors.password).toBeTruthy()
  })

  it('rejects a too-short fullname', () => {
    const result = validateUserInput({ fullname: 'A' })
    expect(result.isValid).toBe(false)
    expect(result.errors.fullname).toBeTruthy()
  })

  it('only validates the provided fields', () => {
    const result = validateUserInput({ email: 'alice@example.com' })
    expect(result.isValid).toBe(true)
  })
})

describe('getUserDisplayName', () => {
  it('returns Guest for null user', () => {
    expect(getUserDisplayName(null)).toBe('Guest')
  })

  it('prefers fullname over email', () => {
    expect(getUserDisplayName({ fullname: 'Alice', email: 'a@b.com' } as User)).toBe('Alice')
  })
})

describe('getUserAvatar', () => {
  it('builds initials from the fullname', () => {
    const avatar = getUserAvatar({ fullname: 'Alice Doe', email: 'a@b.com' } as User)
    expect(avatar).toEqual({ type: 'initials', value: 'AD' })
  })

  it('falls back to G for null user', () => {
    expect(getUserAvatar(null)).toEqual({ type: 'initials', value: 'G' })
  })
})
