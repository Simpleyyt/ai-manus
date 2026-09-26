import { apiClient, ApiResponse } from './client'
import type { ConnectorCatalogItem } from '@/data/connectorCatalog'
import type { Connector, ConnectorWritePayload, VariableItem } from '../types/connector'

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
  headers?: VariableItem[] | null
}

type CatalogConnectorDto = {
  uid: string
  name: string
  brief?: string | null
  icon_url?: string | null
  icon_url_dark?: string | null
  order?: number | null
  url: string
  transport: 'streamable-http' | 'sse'
  required_headers?: { key: string; label?: string | null; placeholder?: string | null }[] | null
}

function toCatalogItem(dto: CatalogConnectorDto): ConnectorCatalogItem {
  return {
    uid: dto.uid,
    name: dto.name,
    brief: dto.brief || '',
    iconUrl: dto.icon_url || '',
    iconUrlDark: dto.icon_url_dark || dto.icon_url || '',
    order: dto.order || 0,
    serverUrl: dto.url,
    transport: dto.transport,
    requiredHeaders: (dto.required_headers || []).map((field) => ({
      key: field.key,
      label: field.label || field.key,
      placeholder: field.placeholder || undefined,
    })),
  }
}

export async function fetchConnectorCatalog(): Promise<ConnectorCatalogItem[]> {
  const response = await apiClient.get<ApiResponse<{ connectors: CatalogConnectorDto[] }>>('/connectors/catalog')
  return (response.data.data.connectors || []).map(toCatalogItem)
}

export async function createFromCatalog(payload: CreateFromCatalogPayload): Promise<Connector> {
  const response = await apiClient.post<ApiResponse<Connector>>('/connectors/from-catalog', payload)
  return response.data.data
}

export async function setConnectorEnabled(id: string, enabled: boolean): Promise<Connector> {
  const response = await apiClient.patch<ApiResponse<Connector>>(`/connectors/${id}/enabled`, { enabled })
  return response.data.data
}
