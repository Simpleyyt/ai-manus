import { ref } from 'vue'
import axios from 'axios'
import {
  createConnector as createConnectorApi,
  createMcpFromUrl as createMcpFromUrlApi,
  deleteConnector as deleteConnectorApi,
  fetchConnectors,
  importMcpJson as importMcpJsonApi,
  updateConnector as updateConnectorApi,
} from '@/api/connectors'
import type { Connector, ConnectorWritePayload } from '@/types/connector'

const connectors = ref<Connector[]>([])
const loading = ref(false)
const loaded = ref(false)
const loadError = ref<string | null>(null)

let loadPromise: Promise<void> | null = null

function applyConnectors(items: Connector[]) {
  connectors.value = items
  loaded.value = true
}

export function connectorErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const msg = error.response?.data?.msg
    if (typeof msg === 'string' && msg.trim()) return msg
  }
  return error instanceof Error ? error.message : fallback
}

export async function reloadConnectors(): Promise<void> {
  loading.value = true
  loadError.value = null
  try {
    applyConnectors(await fetchConnectors())
  } catch (error) {
    loadError.value = connectorErrorMessage(error, 'Failed to load connectors')
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

export function filterConnectorsByQuery(
  query: string,
  source: Connector[] = connectors.value,
): Connector[] {
  const q = query.trim().toLowerCase()
  if (!q) return source
  return source.filter((item) => {
    const note = item.note || ''
    return item.name.toLowerCase().includes(q) || note.toLowerCase().includes(q)
  })
}

export async function createConnector(payload: ConnectorWritePayload): Promise<Connector> {
  const created = await createConnectorApi(payload)
  await reloadConnectors()
  return created
}

export async function updateConnector(
  id: string,
  payload: ConnectorWritePayload,
): Promise<Connector> {
  const updated = await updateConnectorApi(id, payload)
  await reloadConnectors()
  return updated
}

export async function deleteConnector(id: string): Promise<void> {
  await deleteConnectorApi(id)
  await reloadConnectors()
}

export async function importMcpJson(json: string): Promise<Connector> {
  const created = await importMcpJsonApi(json)
  await reloadConnectors()
  return created
}

export async function createMcpFromUrl(url: string, name?: string): Promise<Connector> {
  const created = await createMcpFromUrlApi(url, name)
  await reloadConnectors()
  return created
}

export function resetConnectorsStoreForTests(): void {
  connectors.value = []
  loading.value = false
  loaded.value = false
  loadError.value = null
  loadPromise = null
}

export function setConnectorsStoreForTests(items: Connector[]): void {
  connectors.value = items
  loaded.value = true
}

export { connectors, loading, loaded, loadError }
