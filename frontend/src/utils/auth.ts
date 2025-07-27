// Authentication utility functions
import type { User, UserRole } from '../api/auth'
import { i18n } from '../composables/useI18n'


/**
 * Get user display name
 */
export function getUserDisplayName(user: User | null): string {
  if (!user) return 'Guest'
  return user.fullname || user.email || 'Unknown User'
}

/**
 * Get user role display name
 */
export function getRoleDisplayName(role: UserRole): string {
  const roleNames: Record<UserRole, string> = {
    admin: 'Administrator',
    user: 'User'
  }
  return roleNames[role] || role
}

/**
 * Check if user account is expired or needs attention
 */
export function getUserAccountStatus(user: User | null): {
  isValid: boolean
  isActive: boolean
  needsAttention: boolean
  message?: string
} {
  if (!user) {
    return {
      isValid: false,
      isActive: false,
      needsAttention: true,
      message: 'No user data available'
    }
  }
  
  if (!user.is_active) {
    return {
      isValid: false,
      isActive: false,
      needsAttention: true,
      message: 'Account is deactivated'
    }
  }
  
  return {
    isValid: true,
    isActive: true,
    needsAttention: false
  }
}

/**
 * Format user creation date
 */
export function formatUserDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return 'Invalid date'
  }
}

/**
 * Generate user avatar URL or initials
 */
export function getUserAvatar(user: User | null): {
  type: 'initials' | 'url'
  value: string
} {
  if (!user) {
    return {
      type: 'initials',
      value: 'G'
    }
  }
  
  // Generate initials from fullname or email
  const name = user.fullname || user.email || 'U'
  const initials = name
    .split(/[\s@]/)
    .map((part: string) => part.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('')
  
  return {
    type: 'initials',
    value: initials || 'U'
  }
}

/**
 * Validate user input for registration/profile update
 */
export function validateUserInput(data: {
  fullname?: string
  email?: string
  password?: string
}): {
  isValid: boolean
  errors: Record<string, string>
} {
  const errors: Record<string, string> = {}
  
  // Full name validation
  if (data.fullname !== undefined) {
    if (!data.fullname || data.fullname.trim().length < 2) {
      errors.fullname = i18n.global.t('Full name must be at least 2 characters long')
    } else if (data.fullname.trim().length > 100) {
      errors.fullname = i18n.global.t('Full name must be less than 100 characters')
    }
  }
  
  // Email validation
  if (data.email !== undefined) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!data.email || !emailRegex.test(data.email)) {
      errors.email = i18n.global.t('Please enter a valid email address')
    }
  }
  
  // Password validation
  if (data.password !== undefined) {
    if (!data.password || data.password.length < 6) {
      errors.password = i18n.global.t('Password must be at least 6 characters long')
    }
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
} 