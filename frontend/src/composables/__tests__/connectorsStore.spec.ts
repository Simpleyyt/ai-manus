import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  filterConnectorsByQuery,
  resetConnectorsStoreForTests,
  setConnectorsStoreForTests,
} from '../connectorsStore'
import type { Connector } from '@/types/connector'

vi.mock('@/api/connectors', () => ({
  fetchConnectors: vi.fn(),
  createConnector: vi.fn(),
  updateConnector: vi.fn(),
  deleteConnector: vi.fn(),
  importMcpJson: vi.fn(),
  createMcpFromUrl: vi.fn(),
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
})
