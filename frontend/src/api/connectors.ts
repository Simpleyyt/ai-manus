import { apiClient, ApiResponse } from './client'
import type { Connector, ConnectorWritePayload } from '../types/connector'

export type ListConnectorsResponse = {
  connectors: Connector[]
}

export async function fetchConnectors(): Promise<Connector[]> {
  const response = await apiClient.get<ApiResponse<ListConnectorsResponse>>('/connectors')
  return response.data.data.connectors
}

export async function createConnector(payload: ConnectorWritePayload): Promise<Connector> {
  const response = await apiClient.post<ApiResponse<Connector>>('/connectors', payload)
  return response.data.data
}

export async function updateConnector(id: string, payload: ConnectorWritePayload): Promise<Connector> {
  const response = await apiClient.patch<ApiResponse<Connector>>(`/connectors/${id}`, payload)
  return response.data.data
}

export async function deleteConnector(id: string): Promise<void> {
  await apiClient.delete<ApiResponse<null>>(`/connectors/${id}`)
}

export async function importMcpJson(json: string): Promise<Connector> {
  const response = await apiClient.post<ApiResponse<Connector>>('/connectors/import-json', { json })
  return response.data.data
}

export async function createMcpFromUrl(url: string, name?: string): Promise<Connector> {
  const response = await apiClient.post<ApiResponse<Connector>>('/connectors/from-url', { url, name })
  return response.data.data
}
