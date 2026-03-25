// API modules index
export * from './client';
export * from './auth';
export * from './config';
export * from './agent';
export * from './file';

// Export commonly used types and functions
export type { ApiResponse, ApiError } from './client';
export type { 
  User, 
  LoginRequest, 
  LoginResponse, 
  RegisterRequest, 
  RegisterResponse,
  ChangePasswordRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
  AuthStatusResponse,
  UserRole
} from './auth';

// Import and re-export auth initialization function
import { initializeAuth } from './auth';

// Initialize authentication when module is imported
initializeAuth();

export { initializeAuth };

// Export auth composable
export { useAuth } from '../composables/useAuth'; 