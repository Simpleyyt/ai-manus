import { apiClient, ApiResponse } from './client'

export interface ClientConfigResponse {
  auth_provider: string
  show_github_button: boolean
  github_repository_url: string
  google_analytics_id: string | null
}

let clientConfigCache: ClientConfigResponse | null = null
let isClientConfigLoaded = false
let configLoadFailed = false

/**
 * Get client runtime configuration.
 */
export async function getClientConfig(): Promise<ClientConfigResponse> {
  const response = await apiClient.get<ApiResponse<ClientConfigResponse>>('/config/frontend')
  return response.data.data
}

/**
 * Get client runtime configuration (cached after first call).
 * Returns null when config has not been fetched yet or fetch failed.
 */
export async function getCachedClientConfig(): Promise<ClientConfigResponse | null> {
  if (isClientConfigLoaded) {
    return clientConfigCache
  }

  try {
    clientConfigCache = await getClientConfig()
    isClientConfigLoaded = true
    configLoadFailed = false
    return clientConfigCache
  } catch (error) {
    console.warn('Failed to load client runtime configuration:', error)
    isClientConfigLoaded = true
    configLoadFailed = true
    return null
  }
}

/**
 * Whether the config load has failed (server unreachable, etc.).
 */
export function isConfigLoadFailed(): boolean {
  return configLoadFailed
}

/**
 * Reset cached config so the next call re-fetches from server.
 */
export function resetCachedClientConfig(): void {
  clientConfigCache = null
  isClientConfigLoaded = false
  configLoadFailed = false
}

/**
 * Read auth provider from client configuration.
 */
export async function getCachedAuthProvider(): Promise<string | null> {
  const clientConfig = await getCachedClientConfig()
  return clientConfig?.auth_provider || null
}
