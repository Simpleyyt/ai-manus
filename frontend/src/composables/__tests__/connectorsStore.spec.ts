import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  connectors,
  filterConnectorsByQuery,
  resetConnectorsStoreForTests,
  setConnectorEnabled,
  setConnectorsStoreForTests,
} from '../connectorsStore'
import type { Connector } from '@/types/connector'
import * as api from '@/api/connectors'

vi.mock('@/api/connectors', () => ({
  fetchConnectors: vi.fn(),
  createConnector: vi.fn(),
  updateConnector: vi.fn(),
  deleteConnector: vi.fn(),
  importMcpJson: vi.fn(),
  createMcpFromUrl: vi.fn(),
  setConnectorEnabled: vi.fn(),
}))

const sample: Connector[] = [
  {
    id: 'c1',
    name: 'Docs MCP',
    server_key: 'docs_mcp',
    note: 'Search docs',
    transport: 'streamable-http',
    enabled: true,
    source: 'form',
    readonly: false,
    url: 'https://mcp.example.com/mcp',
  },
  {
    id: 'file:github',
    name: 'github',
    server_key: 'github',
    transport: 'stdio',
    enabled: true,
    source: 'file',
    readonly: true,
    command: 'npx',
  },
]

describe('connectorsStore', () => {
  beforeEach(() => {
    resetConnectorsStoreForTests()
    setConnectorsStoreForTests(sample)
  })

  it('filters connectors by name and note', () => {
    expect(filterConnectorsByQuery('docs').map((item) => item.id)).toEqual(['c1'])
    expect(filterConnectorsByQuery('github').map((item) => item.id)).toEqual(['file:github'])
  })

  it('setConnectorEnabled patches then reloads', async () => {
    vi.mocked(api.setConnectorEnabled).mockResolvedValue({
      ...sample[0],
      enabled: false,
    })
    vi.mocked(api.fetchConnectors).mockResolvedValue([
      { ...sample[0], enabled: false },
      sample[1],
    ])

    await setConnectorEnabled('c1', false)

    expect(api.setConnectorEnabled).toHaveBeenCalledWith('c1', false)
    expect(api.fetchConnectors).toHaveBeenCalled()
    expect(connectors.value.find((item) => item.id === 'c1')?.enabled).toBe(false)
  })
})
