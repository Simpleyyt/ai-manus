import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ConnectorPreview from '../ConnectorPreview.vue'
import { resetCatalogStoreForTests } from '@/composables/catalogStore'
import * as api from '@/api/connectors'
import type { ConnectorCatalogItem } from '@/data/connectorCatalog'

vi.mock('@/api/connectors', () => ({
  fetchConnectorCatalog: vi.fn(),
}))

const previewCatalog: ConnectorCatalogItem[] = [
  {
    uid: 'crypto',
    name: 'Crypto.com',
    brief: '',
    iconUrl: 'https://cdn.example/crypto.png',
    iconUrlDark: 'https://cdn.example/crypto.png',
    order: 23,
    serverUrl: 'https://mcp.crypto.com/market-data/mcp',
    transport: 'streamable-http',
    requiredHeaders: [],
  },
  {
    uid: 'gecko',
    name: 'CoinGecko',
    brief: '',
    iconUrl: 'https://cdn.example/gecko.png',
    iconUrlDark: 'https://cdn.example/gecko.png',
    order: 27,
    serverUrl: 'https://mcp.api.coingecko.com/mcp',
    transport: 'streamable-http',
    requiredHeaders: [],
  },
  {
    uid: 'pop',
    name: 'PopHIVE',
    brief: '',
    iconUrl: 'https://cdn.example/pop.png',
    iconUrlDark: 'https://cdn.example/pop.png',
    order: 50,
    serverUrl: 'https://mcp.pophive.org/mcp',
    transport: 'streamable-http',
    requiredHeaders: [],
  },
]

describe('ConnectorPreview', () => {
  beforeEach(() => {
    resetCatalogStoreForTests()
    vi.mocked(api.fetchConnectorCatalog).mockResolvedValue(previewCatalog)
  })

  it('renders overlapping logos from the catalog returned by the backend', async () => {
    const wrapper = mount(ConnectorPreview)
    await flushPromises()
    const root = wrapper.find('[data-testid="connector-preview"]')
    expect(root.exists()).toBe(true)
    expect(root.classes().join(' ')).toContain('-space-x-1')
    expect(root.text()).toContain('+1')
    const imgs = wrapper.findAll('[data-testid="connector-icon-img"]')
    expect(imgs).toHaveLength(2)
    expect(imgs[0].attributes('alt')).toBe('Crypto.com')
    expect(imgs[1].attributes('alt')).toBe('CoinGecko')
    expect(imgs[0].attributes('src')).toContain('cdn.example/crypto.png')
  })
})
