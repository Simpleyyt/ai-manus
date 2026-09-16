export type ConnectorTransport = 'stdio' | 'sse' | 'streamable-http'

export type ConnectorEnvField = {
  key: string
  label: string
  secret?: boolean
  placeholder?: string
}

export type ConnectorCatalogItem = {
  id: string
  name: string
  description: string
  category: string
  icon_url?: string | null
  transport: ConnectorTransport
  command?: string | null
  args?: string[] | null
  url?: string | null
  env_fields: ConnectorEnvField[]
  header_fields: ConnectorEnvField[]
}

export type ConnectedConnector = {
  id: string
  name: string
  description?: string | null
  icon_url?: string | null
  source: 'builtin' | 'custom'
  catalog_id?: string | null
  transport: ConnectorTransport
  command?: string | null
  args?: string[] | null
  url?: string | null
  headers?: Record<string, string> | null
  env?: Record<string, string> | null
  enabled: boolean
}

export type ConnectorsStateResponse = {
  catalog: ConnectorCatalogItem[]
  connected: ConnectedConnector[]
}
