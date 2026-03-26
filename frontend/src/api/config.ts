import { apiClient, ApiResponse } from './client'

export interface ClientConfigResponse {
  auth_provider: string
  show_github_button: boolean
  github_repository_url: string
  google_analytics_id: string | null
}

let clientConfigCache: ClientConfigResponse | null = null
let isClientConfigLoaded = false

/**
 * Get client runtime configuration.
 */
export async function getClientConfig(): Promise<ClientConfigResponse> {
  const response = await apiClient.get<ApiResponse<ClientConfigResponse>>('/config/frontend')
  return response.data.data
}

/**
 * Get client runtime configuration (cached after first call).
 */
export async function getCachedClientConfig(): Promise<ClientConfigResponse | null> {
  if (isClientConfigLoaded) {
    return clientConfigCache
  }

  try {
    clientConfigCache = await getClientConfig()
    isClientConfigLoaded = true
    return clientConfigCache
  } catch (error) {
    console.warn('Failed to load client runtime configuration:', error)
    return null
  }
}

/**
 * Read auth provider from client configuration.
 */
export async function getCachedAuthProvider(): Promise<string | null> {
  const clientConfig = await getCachedClientConfig()
  return clientConfig?.auth_provider || null
}
