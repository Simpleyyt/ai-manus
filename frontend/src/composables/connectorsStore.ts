import { computed, ref } from 'vue'
import {
  connectBuiltinConnector as connectBuiltinConnectorApi,
  createCustomConnector as createCustomConnectorApi,
  deleteConnector as deleteConnectorApi,
  fetchConnectorsState,
  testConnector as testConnectorApi,
  updateConnector as updateConnectorApi,
} from '@/api/connectors'
import type { ConnectedConnector, ConnectorCatalogItem, ConnectorTransport } from '@/types/connector'

const catalog = ref<ConnectorCatalogItem[]>([])
const connected = ref<ConnectedConnector[]>([])
const loading = ref(false)
const loaded = ref(false)
const loadError = ref<string | null>(null)

let loadPromise: Promise<void> | null = null

function applyState(state: { catalog: ConnectorCatalogItem[]; connected: ConnectedConnector[] }) {
  catalog.value = state.catalog
  connected.value = state.connected
  loaded.value = true
}

export async function reloadConnectors(): Promise<void> {
  loading.value = true
  loadError.value = null
  try {
    applyState(await fetchConnectorsState())
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : 'Failed to load connectors'
    throw error
  } finally {
    loading.value = false
  }
}

export async function ensureConnectorsLoaded(): Promise<void> {
  if (loaded.value) return
  if (!loadPromise) {
    loadPromise = reloadConnectors().finally(() => {
      loadPromise = null
    })
  }
  await loadPromise
}

export const connectorsCatalog = computed(() => catalog.value)
export const connectedConnectors = computed(() => connected.value)
export const customConnectors = computed(() =>
  connected.value.filter((connector) => connector.source === 'custom'),
)

const connectedCatalogIds = computed(() =>
  new Set(connected.value.map((connector) => connector.catalog_id).filter(Boolean)),
)

export function filterConnectorsByQuery(
  query: string,
  source: ConnectorCatalogItem[] | ConnectedConnector[] = connected.value,
) {
  const q = query.trim().toLowerCase()
  if (!q) return source
  return source.filter((item) =>
    item.name.toLowerCase().includes(q) ||
    (item.description || '').toLowerCase().includes(q),
  )
}

export function isConnectorConnected(catalogId: string): boolean {
  return connectedCatalogIds.value.has(catalogId)
}

export function getConnectedByCatalogId(catalogId: string): ConnectedConnector | undefined {
  return connected.value.find((connector) => connector.catalog_id === catalogId)
}

export function getConnectorById(connectorId: string): ConnectedConnector | undefined {
  return connected.value.find((connector) => connector.id === connectorId)
}

export async function connectBuiltin(
  catalogId: string,
  payload: { env?: Record<string, string>; headers?: Record<string, string> },
): Promise<void> {
  applyState(await connectBuiltinConnectorApi(catalogId, payload))
}

export async function createCustomConnector(payload: {
  name: string
  description?: string
  icon_url?: string
  transport: ConnectorTransport
  command?: string
  args?: string[]
  url?: string
  headers?: Record<string, string>
  env?: Record<string, string>
}): Promise<void> {
  applyState(await createCustomConnectorApi(payload))
}

export async function setConnectorEnabled(connectorId: string, enabled: boolean): Promise<void> {
  const updated = await updateConnectorApi(connectorId, { enabled })
  connected.value = connected.value.map((connector) =>
    connector.id === connectorId ? updated : connector,
  )
}

export async function removeConnector(connectorId: string): Promise<void> {
  applyState(await deleteConnectorApi(connectorId))
}

export async function testConnectorConnection(payload: {
  transport: ConnectorTransport
  command?: string
  args?: string[]
  url?: string
  headers?: Record<string, string>
  env?: Record<string, string>
}) {
  return testConnectorApi(payload)
}

export { loading as connectorsLoading, loaded as connectorsLoaded, loadError as connectorsLoadError }
