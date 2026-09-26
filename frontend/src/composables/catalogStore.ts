import { ref } from 'vue'
import { fetchConnectorCatalog } from '@/api/connectors'
import type { ConnectorCatalogItem } from '@/data/connectorCatalog'

const catalogItems = ref<ConnectorCatalogItem[]>([])
const catalogLoaded = ref(false)

export async function reloadCatalog(): Promise<void> {
  try {
    catalogItems.value = await fetchConnectorCatalog()
    catalogLoaded.value = true
  } catch {
    if (!catalogLoaded.value) catalogItems.value = []
  }
}

export function getCatalogItem(uid: string): ConnectorCatalogItem | undefined {
  return catalogItems.value.find((item) => item.uid === uid)
}

export function resetCatalogStoreForTests(): void {
  catalogItems.value = []
  catalogLoaded.value = false
}

export function setCatalogStoreForTests(items: ConnectorCatalogItem[]): void {
  catalogItems.value = items
  catalogLoaded.value = true
}

export { catalogItems, catalogLoaded }
