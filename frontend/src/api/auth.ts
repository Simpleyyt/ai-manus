// Authentication API service
import { apiClient, ApiResponse } from './client';

/**
 * User role type
 */
export type UserRole = 'admin' | 'user';

/**
 * User response type
 */
export interface User {
  id: string;
  fullname: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

/**
 * Login request type
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Register request type
 */
export interface RegisterRequest {
  fullname: string;
  email: string;
  password: string;
}

/**
 * Login response type
 */
export interface LoginResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * Register response type
 */
export interface RegisterResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * Change password request type
 */
export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

/**
 * Change fullname request type
 */
export interface ChangeFullnameRequest {
  fullname: string;
}

/**
 * Refresh token request type
 */
export interface RefreshTokenRequest {
  refresh_token: string;
}

/**
 * Refresh token response type
 */
export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
}

/**
 * Auth status response type
 */
export interface AuthStatusResponse {
  authenticated: boolean;
  user?: User;
  auth_provider: string;
}

/**
 * Resource access token request type
 */
export interface AccessTokenRequest {
  resource_type: 'file' | 'vnc';
  resource_id: string;
  expire_minutes?: number;
}

/**
 * Resource access token response type
 */
export interface AccessTokenResponse {
  access_token: string;
  resource_type: string;
  resource_id: string;
  expires_in: number;
}

/**
 * Send verification code request type
 */
export interface SendVerificationCodeRequest {
  email: string;
}

/**
 * Reset password request type
 */
export interface ResetPasswordRequest {
  email: string;
  verification_code: string;
  new_password: string;
}



/**
 * User login
 * @param request Login credentials
 * @returns Login response with user info and tokens
 */
export async function login(request: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<ApiResponse<LoginResponse>>('/auth/login', request);
  return response.data.data;
}

/**
 * User registration
 * @param request Registration data
 * @returns Registration response with user info and tokens
 */
export async function register(request: RegisterRequest): Promise<RegisterResponse> {
  const response = await apiClient.post<ApiResponse<RegisterResponse>>('/auth/register', request);
  return response.data.data;
}

/**
 * Get authentication status
 * @returns Current authentication status and configuration
 */
export async function getAuthStatus(): Promise<AuthStatusResponse> {
  const response = await apiClient.get<ApiResponse<AuthStatusResponse>>('/auth/status');
  return response.data.data;
}

/**
 * Change user password
 * @param request Change password data
 * @returns Success response
 */
export async function changePassword(request: ChangePasswordRequest): Promise<{}> {
  const response = await apiClient.post<ApiResponse<{}>>('/auth/change-password', request);
  return response.data.data;
}

/**
 * Change user fullname
 * @param request Change fullname data
 * @returns Updated user data
 */
export async function changeFullname(request: ChangeFullnameRequest): Promise<User> {
  const response = await apiClient.post<ApiResponse<User>>('/auth/change-fullname', request);
  return response.data.data;
}

/**
 * Get current user information
 * @returns Current user data
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<ApiResponse<User>>('/auth/me');
  return response.data.data;
}

/**
 * Get user by ID (admin only)
 * @param userId User ID to fetch
 * @returns User data
 */
export async function getUser(userId: string): Promise<User> {
  const response = await apiClient.get<ApiResponse<User>>(`/auth/user/${userId}`);
  return response.data.data;
}

/**
 * Deactivate user account (admin only)
 * @param userId User ID to deactivate
 * @returns Success response
 */
export async function deactivateUser(userId: string): Promise<{}> {
  const response = await apiClient.post<ApiResponse<{}>>(`/auth/user/${userId}/deactivate`);
  return response.data.data;
}

/**
 * Activate user account (admin only)
 * @param userId User ID to activate
 * @returns Success response
 */
export async function activateUser(userId: string): Promise<{}> {
  const response = await apiClient.post<ApiResponse<{}>>(`/auth/user/${userId}/activate`);
  return response.data.data;
}

/**
 * Refresh access token
 * @param request Refresh token data
 * @returns New access token
 */
export async function refreshToken(request: RefreshTokenRequest): Promise<RefreshTokenResponse> {
  const response = await apiClient.post<ApiResponse<RefreshTokenResponse>>('/auth/refresh', request);
  return response.data.data;
}

/**
 * User logout
 * @returns Success response
 */
export async function logout(): Promise<{}> {
  const response = await apiClient.post<ApiResponse<{}>>('/auth/logout');
  return response.data.data;
}

/**
 * Send verification code for password reset
 * @param request Email to send verification code to
 * @returns Success response
 */
export async function sendVerificationCode(request: SendVerificationCodeRequest): Promise<{}> {
  const response = await apiClient.post<ApiResponse<{}>>('/auth/send-verification-code', request);
  return response.data.data;
}

/**
 * Reset password with verification code
 * @param request Reset password data including email, verification code and new password
 * @returns Success response
 */
export async function resetPassword(request: ResetPasswordRequest): Promise<{}> {
  const response = await apiClient.post<ApiResponse<{}>>('/auth/reset-password', request);
  return response.data.data;
}



/**
 * Set authentication token in request headers
 * @param token JWT access token
 */
export function setAuthToken(token: string): void {
  apiClient.defaults.headers.Authorization = `Bearer ${token}`;
}

/**
 * Clear authentication token from request headers
 */
export function clearAuthToken(): void {
  delete apiClient.defaults.headers.Authorization;
}

/**
 * Get stored authentication token from localStorage
 * @returns Stored token or null
 */
export function getStoredToken(): string | null {
  return localStorage.getItem('access_token');
}

/**
 * Store authentication token in localStorage
 * @param token Token to store
 */
export function storeToken(token: string): void {
  localStorage.setItem('access_token', token);
}

/**
 * Store refresh token in localStorage
 * @param refreshToken Refresh token to store
 */
export function storeRefreshToken(refreshToken: string): void {
  localStorage.setItem('refresh_token', refreshToken);
}

/**
 * Get stored refresh token from localStorage
 * @returns Stored refresh token or null
 */
export function getStoredRefreshToken(): string | null {
  return localStorage.getItem('refresh_token');
}

/**
 * Clear stored tokens from localStorage
 */
export function clearStoredTokens(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

/**
 * Initialize authentication from stored tokens
 * This should be called when the app starts
 */
export function initializeAuth(): void {
  const token = getStoredToken();
  if (token) {
    setAuthToken(token);
  }
}

// Auth provider cache
let authProviderCache: string | null = null
let isAuthProviderLoaded = false

/**
 * Get auth provider configuration (cached after first call)
 * @returns Auth provider string or null if failed to load
 */
export async function getCachedAuthProvider(): Promise<string | null> {
  // Return cached value if already loaded
  if (isAuthProviderLoaded) {
    return authProviderCache
  }
  
  // Load auth provider configuration
  try {
    const authStatus = await getAuthStatus()
    authProviderCache = authStatus.auth_provider
    isAuthProviderLoaded = true
    return authProviderCache
  } catch (error) {
    console.warn('Failed to load auth provider configuration:', error)
    // Don't set isAuthProviderLoaded to true on error, allow retry
    return null
  }
} 