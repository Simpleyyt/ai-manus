import { describe, it, expect } from 'vitest'
import {
  catalogByTab,
  catalogInstallBlockReason,
  catalogNeedsSecrets,
  CONNECTOR_IDS,
  featuredCatalogItems,
  getCatalogItem,
  installableCatalogByTab,
  isCatalogInstallable,
  previewCatalogItems,
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
    expect(apps[0].name).toBe('My Browser')
    expect(apps.find((item) => item.name === 'Apify')?.order).toBe(0)
    expect(apps[apps.length - 1]?.order).toBe(0)
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

  it('omits OAuth, BUILTIN, and BYOK from the installable marketplace list', () => {
    const apps = installableCatalogByTab('apps')
    expect(apps.slice(0, 6).map((item) => item.name)).toEqual([
      'Crypto.com',
      'CoinGecko',
      'PopHIVE',
      'Neimo',
      'TomTom Maps',
      'ilert',
    ])
    expect(apps.every(isCatalogInstallable)).toBe(true)
    expect(apps.find((item) => item.name === 'Gmail')).toBeUndefined()
    expect(apps.find((item) => item.name === 'GitHub')).toBeUndefined()
    expect(installableCatalogByTab('api')).toEqual([])
    expect(featuredCatalogItems().filter(isCatalogInstallable)).toEqual([])
    expect(previewCatalogItems()[0]?.name).toBe('Crypto.com')
    expect(previewCatalogItems().length).toBe(apps.length)
    const learn = getCatalogItem(CONNECTOR_IDS.microsoftLearn)!
    const gecko = getCatalogItem(CONNECTOR_IDS.coinGecko)!
    const tomtom = getCatalogItem(CONNECTOR_IDS.tomTomMaps)!
    const gmail = getCatalogItem(CONNECTOR_IDS.gmail)!
    const notion = getCatalogItem(CONNECTOR_IDS.notion)!
    expect(isCatalogInstallable(learn)).toBe(true)
    expect(isCatalogInstallable(gecko)).toBe(true)
    expect(catalogNeedsSecrets(learn)).toBe(false)
    expect(catalogNeedsSecrets(tomtom)).toBe(true)
    expect(catalogInstallBlockReason(learn)).toBeNull()
    expect(catalogInstallBlockReason(gmail)).toBe('OAuth marketplace apps are not wired yet.')
    expect(catalogInstallBlockReason(notion)).toBe('This app requires a sign-in we do not support yet.')
    expect(isCatalogInstallable(gmail)).toBe(false)
  })
})
