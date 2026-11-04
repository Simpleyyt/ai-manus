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
  order: number
  serverUrl: string
  transport: 'streamable-http' | 'sse'
  requiredHeaders: CatalogHeaderField[]
}

/** order 0 last, otherwise ascending; equal keys keep the given order. */
export function sortConnectorsByOrder<T extends { order: number }>(items: T[]): T[] {
  return [...items].sort((left, right) => {
    if (left.order === 0 && right.order === 0) return 0
    if (left.order === 0) return 1
    if (right.order === 0) return -1
    return left.order - right.order
  })
}

export function filterCatalogByQuery(
  query: string,
  source: ConnectorCatalogItem[],
): ConnectorCatalogItem[] {
  const q = query.trim().toLowerCase()
  if (!q) return source
  return source.filter((item) => (
    item.name.toLowerCase().includes(q) || item.brief.toLowerCase().includes(q)
  ))
}

export function catalogNeedsSecrets(item: ConnectorCatalogItem): boolean {
  return item.requiredHeaders.length > 0
}

export function isCatalogUidInstalled(
  uid: string,
  items: { catalog_uid?: string | null }[],
): boolean {
  return items.some((item) => item.catalog_uid === uid)
}
