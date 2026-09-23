import { apiClient, ApiResponse } from './client'
import type { Connector, ConnectorTransport, ConnectorWritePayload, VariableItem } from '../types/connector'

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

export type CreateFromCatalogPayload = {
  catalog_uid: string
  name: string
  url: string
  transport: ConnectorTransport
  icon_url?: string | null
  note?: string | null
  headers?: VariableItem[] | null
}

export async function createFromCatalog(payload: CreateFromCatalogPayload): Promise<Connector> {
  const response = await apiClient.post<ApiResponse<Connector>>('/connectors/from-catalog', payload)
  return response.data.data
}

export async function setConnectorEnabled(id: string, enabled: boolean): Promise<Connector> {
  const response = await apiClient.patch<ApiResponse<Connector>>(`/connectors/${id}/enabled`, { enabled })
  return response.data.data
}
