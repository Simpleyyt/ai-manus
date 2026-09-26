import { onMounted } from 'vue'
import {
  connectors,
  createConnector,
  createFromCatalog,
  createMcpFromUrl,
  deleteConnector,
  ensureConnectorsLoaded,
  filterConnectorsByQuery,
  importMcpJson,
  loadError,
  loaded,
  loading,
  reloadConnectors,
  setConnectorEnabled,
  updateConnector,
} from './connectorsStore'

export function useConnectors() {
  onMounted(() => {
    void ensureConnectorsLoaded()
  })

  return {
    connectors,
    loading,
    loaded,
    loadError,
    filterByQuery: filterConnectorsByQuery,
    createConnector,
    updateConnector,
    deleteConnector,
    importMcpJson,
    createMcpFromUrl,
    createFromCatalog,
    setConnectorEnabled,
    reloadConnectors,
    ensureConnectorsLoaded,
  }
}
