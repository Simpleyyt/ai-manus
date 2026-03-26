import { apiClient, ApiResponse } from './client'

export interface ClientConfigResponse {
  auth_provider: string
  show_github_button: boolean
  github_repository_url: string
}

let clientConfigCache: ClientConfigResponse | null = null
let clientConfigPromise: Promise<ClientConfigResponse | null> | null = null

/**
 * Fetch client runtime configuration from the server (no caching).
 */
export async function getClientConfig(): Promise<ClientConfigResponse> {
  const response = await apiClient.get<ApiResponse<ClientConfigResponse>>('/config/frontend')
  return response.data.data
}

/**
 * Load and cache client runtime configuration.
 * Concurrent calls share a single in-flight request.
 * On failure the promise is cleared so the next call retries.
 */
export async function getCachedClientConfig(): Promise<ClientConfigResponse | null> {
  if (clientConfigCache) {
    return clientConfigCache
  }

  if (!clientConfigPromise) {
    clientConfigPromise = getClientConfig()
      .then(config => {
        clientConfigCache = config
        return config
      })
      .catch(error => {
        console.warn('Failed to load client runtime configuration:', error)
        clientConfigPromise = null
        return null
      })
  }

  return clientConfigPromise
}

/**
 * Synchronous read of the cached auth provider value.
 * Returns null when the config has not been loaded yet.
 */
export function getAuthProvider(): string | null {
  return clientConfigCache?.auth_provider ?? null
}

/**
 * Synchronous read of the full cached client config.
 */
export function getClientConfigSync(): ClientConfigResponse | null {
  return clientConfigCache
}

/**
 * Read auth provider from client configuration (async, triggers fetch if needed).
 */
export async function getCachedAuthProvider(): Promise<string | null> {
  const clientConfig = await getCachedClientConfig()
  return clientConfig?.auth_provider || null
}
