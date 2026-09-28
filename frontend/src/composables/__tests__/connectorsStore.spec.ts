import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  connectors,
  createFromCatalog,
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
  createFromCatalog: vi.fn(),
  fetchConnectorCatalog: vi.fn(),
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
    id: 'github-1',
    name: 'github',
    server_key: 'github',
    transport: 'stdio',
    enabled: true,
    source: 'form',
    readonly: false,
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
    expect(filterConnectorsByQuery('github').map((item) => item.id)).toEqual(['github-1'])
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

  it('createFromCatalog reloads the store', async () => {
    const created: Connector = {
      id: 'learn-1',
      name: 'Microsoft Learn',
      server_key: 'microsoft_learn',
      catalog_uid: 'f4c2516f-40c3-4be2-b1c6-fb18da6a04bf',
      transport: 'streamable-http',
      enabled: true,
      source: 'catalog',
      readonly: false,
      url: 'https://learn.microsoft.com/api/mcp',
    }
    vi.mocked(api.createFromCatalog).mockResolvedValue(created)
    vi.mocked(api.fetchConnectors).mockResolvedValue([...sample, created])

    const result = await createFromCatalog({
      catalog_uid: created.catalog_uid!,
    })

    expect(result.id).toBe('learn-1')
    expect(api.createFromCatalog).toHaveBeenCalled()
    expect(connectors.value.some((item) => item.catalog_uid === created.catalog_uid)).toBe(true)
  })
})
