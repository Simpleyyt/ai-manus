import { describe, it, expect } from 'vitest'
import {
  catalogNeedsSecrets,
  filterCatalogByQuery,
  sortConnectorsByOrder,
  type ConnectorCatalogItem,
} from '../connectorCatalog'

function item(partial: Partial<ConnectorCatalogItem> & Pick<ConnectorCatalogItem, 'uid' | 'name'>): ConnectorCatalogItem {
  return {
    brief: '',
    iconUrl: '',
    iconUrlDark: '',
    order: 0,
    serverUrl: 'https://example.com/mcp',
    transport: 'streamable-http',
    requiredHeaders: [],
    ...partial,
  }
}

describe('connectorCatalog', () => {
  it('places order 0 after positive orders', () => {
    const sorted = sortConnectorsByOrder([
      { order: 0, name: 'z' },
      { order: 2, name: 'a' },
      { order: 0, name: 'y' },
      { order: 1, name: 'b' },
    ])
    expect(sorted.map((entry) => entry.name)).toEqual(['b', 'a', 'z', 'y'])
  })

  it('filters by name and brief and treats header fields as secrets', () => {
    const learn = item({ uid: 'learn', name: 'Microsoft Learn', brief: 'docs' })
    const tomtom = item({
      uid: 'tomtom',
      name: 'TomTom Maps',
      brief: 'maps',
      requiredHeaders: [{ key: 'tomtom-api-key', label: 'API Key' }],
    })
    expect(filterCatalogByQuery('docs', [learn, tomtom]).map((entry) => entry.uid)).toEqual(['learn'])
    expect(catalogNeedsSecrets(learn)).toBe(false)
    expect(catalogNeedsSecrets(tomtom)).toBe(true)
  })
})
