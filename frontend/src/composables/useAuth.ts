import { ref, computed, onMounted } from 'vue'
import { 
  login as apiLogin, 
  register as apiRegister, 
  logout as apiLogout,
  getCurrentUser,
  refreshToken as apiRefreshToken,
  setAuthToken,
  clearAuthToken,
  storeToken,
  storeRefreshToken,
  getStoredToken,
  getStoredRefreshToken,
  clearStoredTokens,
  type User,
  type LoginRequest,
  type RegisterRequest,
  type LoginResponse,
  type RegisterResponse
} from '../api/auth'
import { getCachedAuthProvider } from '../api/config'

// Global auth state
const currentUser = ref<User | null>(null)
const isAuthenticated = ref<boolean>(false)
const isLoading = ref<boolean>(false)
const authError = ref<string | null>(null)

export function useAuth() {
  /**
   * Initialize authentication state
   */
  const initAuth = async () => {
    // Get auth provider configuration (cached after first call)
    const authProvider = await getCachedAuthProvider()
    
    if (authProvider === 'none') {
      // No authentication required, set as authenticated with anonymous user
      currentUser.value = {
        id: 'anonymous',
        fullname: 'Anonymous User',
        email: 'anonymous@localhost',
        role: 'user',
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
      isAuthenticated.value = true
      return
    }
    
    // For other auth providers, check token
    const token = getStoredToken()
    if (token) {
      setAuthToken(token)
      await loadCurrentUser()
    }
  }

  /**
   * Load current user information
   */
  const loadCurrentUser = async () => {
    try {
      isLoading.value = true
      authError.value = null
      const user = await getCurrentUser()
      currentUser.value = user
      isAuthenticated.value = true
    } catch (error: any) {
      console.error('Failed to load current user:', error)
      // If token is invalid, clear auth state
      clearAuth()
      authError.value = error.message || 'Failed to load user information'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * User login
   */
  const login = async (credentials: LoginRequest): Promise<LoginResponse> => {
    try {
      isLoading.value = true
      authError.value = null
      
      const response = await apiLogin(credentials)
      
      // Store tokens
      storeToken(response.access_token)
      storeRefreshToken(response.refresh_token)
      setAuthToken(response.access_token)
      
      // Update user state
      currentUser.value = response.user
      isAuthenticated.value = true
      
      return response
    } catch (error: any) {
      authError.value = error.message || 'Login failed'
      throw error
    } finally {
      isLoading.value = false
    }
  }

  /**
   * User registration
   */
  const register = async (data: RegisterRequest): Promise<RegisterResponse> => {
    try {
      isLoading.value = true
      authError.value = null
      
      const response = await apiRegister(data)
      
      // Store tokens
      storeToken(response.access_token)
      storeRefreshToken(response.refresh_token)
      setAuthToken(response.access_token)
      
      // Update user state
      currentUser.value = response.user
      isAuthenticated.value = true
      
      return response
    } catch (error: any) {
      authError.value = error.message || 'Registration failed'
      throw error
    } finally {
      isLoading.value = false
    }
  }

  /**
   * User logout
   */
  const logout = async (silent: boolean = false) => {
    try {
      if (!silent) {
        isLoading.value = true
        authError.value = null
        
        // Call logout API
        await apiLogout()
      }
    } catch (error: any) {
      console.error('Logout API failed:', error)
      // Continue with local logout even if API fails
    } finally {
      // Clear local auth state
      clearAuth()
      isLoading.value = false
    }
  }

  /**
   * Clear authentication state
   */
  const clearAuth = () => {
    currentUser.value = null
    isAuthenticated.value = false
    clearAuthToken()
    clearStoredTokens()
    authError.value = null
  }

  /**
   * Refresh authentication token
   */
  const refreshAuthToken = async (): Promise<boolean> => {
    const refreshToken = getStoredRefreshToken()
    if (!refreshToken) {
      clearAuth()
      return false
    }

    try {
      const response = await apiRefreshToken({ refresh_token: refreshToken })
      
      // Store new access token
      storeToken(response.access_token)
      setAuthToken(response.access_token)
      
      return true
    } catch (error: any) {
      console.error('Token refresh failed:', error)
      clearAuth()
      return false
    }
  }

  /**
   * Check if user has specific role
   */
  const hasRole = (role: string): boolean => {
    return currentUser.value?.role === role
  }

  /**
   * Check if user is admin
   */
  const isAdmin = computed(() => hasRole('admin'))

  /**
   * Check if user account is active
   */
  const isActive = computed(() => currentUser.value?.is_active === true)

  /**
   * Clear authentication error
   */
  const clearError = () => {
    authError.value = null
  }

  // Listen for logout events from token refresh interceptor
  onMounted(() => {
    window.addEventListener('auth:logout', () => {
      logout(true) // Silent logout
    })
  })

  // Auto-initialize auth state when composable is first used
  if (!isAuthenticated.value && !isLoading.value) {
    initAuth()
  }

  return {
    // State
    currentUser: computed(() => currentUser.value),
    isAuthenticated: computed(() => isAuthenticated.value),
    isLoading: computed(() => isLoading.value),
    authError: computed(() => authError.value),
    isAdmin,
    isActive,
    
    // Actions
    login,
    register,
    logout,
    initAuth,
    loadCurrentUser,
    refreshAuthToken,
    hasRole,
    clearError,
    clearAuth
  }
} 