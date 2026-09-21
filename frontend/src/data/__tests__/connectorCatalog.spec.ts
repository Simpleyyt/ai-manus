import { describe, it, expect } from 'vitest'
import {
  catalogByTab,
  CONNECTOR_IDS,
  featuredCatalogItems,
  sortConnectorsByOrder,
} from '../connectorCatalog'

describe('connectorCatalog', () => {
  it('sorts Apps like official sortConnectorsByOrder (stable, order 0 last)', () => {
    const apps = catalogByTab('apps')
    expect(apps.slice(0, 12).map((item) => item.name)).toEqual([
      'My Browser',
      'Gmail',
      'GitHub',
      'Instagram',
      'Google Workspace',
      'Meta Ads Manager',
      'Google Calendar',
      'Notion',
      'Instagram Creator Marketplace',
      'Higgsfield',
      'Outlook Mail',
      'TikTok for Business',
    ])
    expect(apps.find((item) => item.name === 'Apify')).toBeUndefined()
  })

  it('keeps FEATURED Connect-apps order without computerUse', () => {
    expect(featuredCatalogItems().map((item) => item.uid)).toEqual([
      CONNECTOR_IDS.github,
      CONNECTOR_IDS.gmail,
      CONNECTOR_IDS.myBrowser,
      CONNECTOR_IDS.metaAdsManager,
      CONNECTOR_IDS.instagram,
      CONNECTOR_IDS.metaCreators,
      CONNECTOR_IDS.outlookMail,
      CONNECTOR_IDS.googleCalendar,
      CONNECTOR_IDS.outlookCalendar,
      CONNECTOR_IDS.googleWorkspace,
      CONNECTOR_IDS.shopify,
    ])
  })

  it('places order 0 after positive orders', () => {
    const sorted = sortConnectorsByOrder([
      { order: 0, name: 'z' },
      { order: 2, name: 'a' },
      { order: 0, name: 'y' },
      { order: 1, name: 'b' },
    ])
    expect(sorted.map((item) => item.name)).toEqual(['b', 'a', 'z', 'y'])
  })
})
