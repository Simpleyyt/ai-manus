import catalogJson from './connectorCatalog.json'

export type ConnectorCatalogTab = 'apps' | 'api'
export type ConnectorCatalogKind = 'mcp' | 'builtin' | 'byok'
export type ConnectorCatalogTransport = 'streamable-http' | 'sse'

export type CatalogHeaderField = {
  key: string
  label: string
  placeholder?: string
}

export type ConnectorCatalogItem = {
  uid: string
  name: string
  brief: string
  iconUrl: string
  iconUrlDark: string
  beta: boolean
  order: number
  tab: ConnectorCatalogTab
  kind: ConnectorCatalogKind
  instantOauth: boolean
  serverUrl: string | null
  transport: ConnectorCatalogTransport | null
  requiredHeaders: CatalogHeaderField[]
}

/** Official CONNECTOR_IDS (module 296284) — computerUse skipped (addon, not Apps). */
export const CONNECTOR_IDS = {
  metaCreators: '9777f7bd-4ca3-431a-98d6-a7ed5221dd81',
  instagram: '4b899211-fd12-410e-a8d2-264a409cbc78',
  metaAdsManager: 'c073ede4-35a7-4c89-8158-c9b40c489932',
  myBrowser: 'be268223-40b2-4f3c-a907-c12eb1699283',
  outlookMail: 'd485c6dd-4939-40fb-9c4a-c9821971468b',
  notion: '9c27c684-2f4f-4d33-8fcf-51664ea15c00',
  github: 'bbb0df76-66bd-4a24-ae4f-2aac4750d90b',
  gmail: '9444d960-ab7e-450f-9cb9-b9467fb0adda',
  googleCalendar: 'dd5abf31-7ad3-4c0b-9b9a-f0a576645baf',
  outlookCalendar: '4bca3029-d276-4644-898d-578a723361b2',
  googleWorkspace: 'f8900a57-4bd7-46cc-83a3-5ebd2420a817',
  shopify: '8b81dcd8-d524-48ff-8360-7065e3088f57',
  microsoftLearn: 'f4c2516f-40c3-4be2-b1c6-fb18da6a04bf',
  coinGecko: '0fc956e1-3d91-4e38-9f04-158adf39e99f',
  tomTomMaps: '15027330-caa8-49d2-8c90-75397e2c6410',
} as const

/** Official CONNECTOR_FEATURED order without computerUse. */
export const CONNECTOR_FEATURED: string[] = [
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
]

/** Official CONNECTOR_PREVIEW — overlapping logos on Add connectors. */
export const CONNECTOR_PREVIEW: string[] = [
  CONNECTOR_IDS.outlookMail,
  CONNECTOR_IDS.notion,
]

export const CONNECTOR_CATALOG: ConnectorCatalogItem[] = catalogJson as ConnectorCatalogItem[]

const catalogByUid = new Map(CONNECTOR_CATALOG.map((item) => [item.uid, item]))

export function getCatalogItem(uid: string): ConnectorCatalogItem | undefined {
  return catalogByUid.get(uid)
}

/** Official connectorsSliceUtils.sortConnectorsByOrder — order 0 last, otherwise stable. */
export function sortConnectorsByOrder<T extends { order: number }>(items: T[]): T[] {
  return [...items].sort((left, right) => {
    if (left.order === 0 && right.order === 0) return 0
    if (left.order === 0) return 1
    if (right.order === 0) return -1
    return left.order - right.order
  })
}

export function catalogByTab(tab: ConnectorCatalogTab): ConnectorCatalogItem[] {
  return sortConnectorsByOrder(CONNECTOR_CATALOG.filter((item) => item.tab === tab))
}

export function featuredCatalogItems(): ConnectorCatalogItem[] {
  return CONNECTOR_FEATURED
    .map((uid) => catalogByUid.get(uid))
    .filter((item): item is ConnectorCatalogItem => Boolean(item))
}

/** Marketplace cards we can actually install — OAuth / BUILTIN / BYOK stay out of the UI. */
export function installableCatalogByTab(tab: ConnectorCatalogTab): ConnectorCatalogItem[] {
  return catalogByTab(tab).filter(isCatalogInstallable)
}

export function previewCatalogItems(): ConnectorCatalogItem[] {
  return installableCatalogByTab('apps')
}

export function filterCatalogByQuery(
  query: string,
  source: ConnectorCatalogItem[] = CONNECTOR_CATALOG,
): ConnectorCatalogItem[] {
  const q = query.trim().toLowerCase()
  if (!q) return source
  return source.filter((item) => (
    item.name.toLowerCase().includes(q) || item.brief.toLowerCase().includes(q)
  ))
}

/** Public MCP URL, no OAuth — Plus creates a real Custom MCP. */
export function isCatalogInstallable(item: ConnectorCatalogItem): boolean {
  return (
    item.kind === 'mcp'
    && Boolean(item.serverUrl)
    && Boolean(item.transport)
    && !item.instantOauth
  )
}

export function catalogNeedsSecrets(item: ConnectorCatalogItem): boolean {
  return isCatalogInstallable(item) && item.requiredHeaders.length > 0
}

export function isCatalogUidInstalled(
  uid: string,
  items: { catalog_uid?: string | null }[],
): boolean {
  return items.some((item) => item.catalog_uid === uid)
}

/** Honest block reason — never fake OAuth / BYOK / missing URL. */
export function catalogInstallBlockReason(item: ConnectorCatalogItem): string | null {
  if (isCatalogInstallable(item)) return null
  if (item.kind === 'builtin') return 'OAuth marketplace apps are not wired yet.'
  if (item.kind === 'byok') return 'Custom API marketplace install is not wired yet.'
  if (item.instantOauth) return 'This app requires a sign-in we do not support yet.'
  return 'This marketplace MCP has no public server URL, so it cannot be installed here.'
}
