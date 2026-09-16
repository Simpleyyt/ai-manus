import { onMounted } from 'vue'
import {
  connectors,
  createConnector,
  createMcpFromUrl,
  deleteConnector,
  ensureConnectorsLoaded,
  filterConnectorsByQuery,
  importMcpJson,
  loadError,
  loaded,
  loading,
  reloadConnectors,
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
    reloadConnectors,
    ensureConnectorsLoaded,
  }
}
