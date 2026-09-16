import { onMounted } from 'vue'
import {
  connectBuiltin,
  connectedConnectors,
  connectorsCatalog,
  connectorsLoaded,
  connectorsLoadError,
  connectorsLoading,
  createCustomConnector,
  customConnectors,
  ensureConnectorsLoaded,
  filterConnectorsByQuery,
  getConnectedByCatalogId,
  getConnectorById,
  isConnectorConnected,
  reloadConnectors,
  removeConnector,
  setConnectorEnabled,
  testConnectorConnection,
} from './connectorsStore'

export function useConnectors() {
  onMounted(() => {
    void ensureConnectorsLoaded()
  })

  return {
    catalog: connectorsCatalog,
    connected: connectedConnectors,
    customConnectors,
    loading: connectorsLoading,
    loaded: connectorsLoaded,
    loadError: connectorsLoadError,
    filterByQuery: filterConnectorsByQuery,
    isConnected: isConnectorConnected,
    getConnectedByCatalogId,
    getConnectorById,
    connectBuiltin,
    createCustomConnector,
    setConnectorEnabled,
    removeConnector,
    testConnectorConnection,
    reloadConnectors,
    ensureConnectorsLoaded,
  }
}
