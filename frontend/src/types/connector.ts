export type ConnectorTransport = 'stdio' | 'sse' | 'streamable-http'
export type ConnectorSource = 'form' | 'json' | 'url' | 'file'

export type VariableItem = {
  key: string
  value: string
}

export type Connector = {
  id: string
  name: string
  server_key: string
  note?: string | null
  icon_url?: string | null
  transport: ConnectorTransport
  enabled: boolean
  source: ConnectorSource
  readonly: boolean
  command?: string | null
  args?: string[] | null
  env?: VariableItem[] | null
  url?: string | null
  headers?: VariableItem[] | null
}

export type ConnectorWritePayload = {
  name: string
  note?: string | null
  transport: ConnectorTransport
  command?: string | null
  args?: string[] | null
  env?: VariableItem[] | null
  url?: string | null
  headers?: VariableItem[] | null
}
