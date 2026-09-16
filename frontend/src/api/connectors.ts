import { apiClient, ApiResponse } from './client'
import type {
  ConnectedConnector,
  ConnectorTransport,
  ConnectorsStateResponse,
} from '@/types/connector'

export async function fetchConnectorsState(): Promise<ConnectorsStateResponse> {
  const response = await apiClient.get<ApiResponse<ConnectorsStateResponse>>('/connectors')
  return response.data.data
}

export async function connectBuiltinConnector(
  catalogId: string,
  payload: { env?: Record<string, string>; headers?: Record<string, string> },
): Promise<ConnectorsStateResponse> {
  const response = await apiClient.post<ApiResponse<ConnectorsStateResponse>>('/connectors/builtin', {
    catalog_id: catalogId,
    ...payload,
  })
  return response.data.data
}

export async function createCustomConnector(payload: {
  name: string
  description?: string
  icon_url?: string
  transport: ConnectorTransport
  command?: string
  args?: string[]
  url?: string
  headers?: Record<string, string>
  env?: Record<string, string>
}): Promise<ConnectorsStateResponse> {
  const response = await apiClient.post<ApiResponse<ConnectorsStateResponse>>('/connectors/custom', payload)
  return response.data.data
}

export async function updateConnector(
  connectorId: string,
  payload: Partial<{
    enabled: boolean
    name: string
    description: string
    transport: ConnectorTransport
    command: string
    args: string[]
    url: string
    headers: Record<string, string>
    env: Record<string, string>
  }>,
): Promise<ConnectedConnector> {
  const response = await apiClient.patch<ApiResponse<ConnectedConnector>>(
    `/connectors/connected/${connectorId}`,
    payload,
  )
  return response.data.data
}

export async function deleteConnector(connectorId: string): Promise<ConnectorsStateResponse> {
  const response = await apiClient.delete<ApiResponse<ConnectorsStateResponse>>(
    `/connectors/connected/${connectorId}`,
  )
  return response.data.data
}

export async function testConnector(payload: {
  transport: ConnectorTransport
  command?: string
  args?: string[]
  url?: string
  headers?: Record<string, string>
  env?: Record<string, string>
}): Promise<{ success: boolean; message: string; tools: string[] }> {
  const response = await apiClient.post<ApiResponse<{ success: boolean; message: string; tools: string[] }>>(
    '/connectors/test',
    payload,
  )
  return response.data.data
}
