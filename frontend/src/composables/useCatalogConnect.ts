import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ConnectorCatalogItem } from '@/data/connectorCatalog'
import {
  catalogNeedsSecrets,
  isCatalogUidInstalled,
} from '@/data/connectorCatalog'
import type { VariableItem } from '@/types/connector'
import {
  connectors,
  createFromCatalog,
  connectorErrorMessage,
} from './connectorsStore'
import { showErrorToast, showSuccessToast } from '@/utils/toast'

export function useCatalogConnect() {
  const { t } = useI18n()
  const secretsItem = ref<ConnectorCatalogItem | null>(null)
  const secretsOpen = ref(false)
  const installingUid = ref<string | null>(null)

  const installedUids = computed(() => (
    new Set(
      connectors.value
        .map((item) => item.catalog_uid)
        .filter((uid): uid is string => Boolean(uid)),
    )
  ))

  const isInstalled = (uid: string) => (
    installedUids.value.has(uid) || isCatalogUidInstalled(uid, connectors.value)
  )

  const installPayload = (item: ConnectorCatalogItem, headers?: VariableItem[]) => ({
    catalog_uid: item.uid,
    headers: headers?.length ? headers : null,
  })

  const install = async (item: ConnectorCatalogItem, headers?: VariableItem[]): Promise<boolean> => {
    installingUid.value = item.uid
    try {
      await createFromCatalog(installPayload(item, headers))
      showSuccessToast(t('Successfully created connector'))
      return true
    } catch (error) {
      showErrorToast(connectorErrorMessage(error, t('Failed to import MCP connector')))
      return false
    } finally {
      installingUid.value = null
    }
  }

  const connect = async (item: ConnectorCatalogItem) => {
    if (isInstalled(item.uid) || installingUid.value === item.uid) return
    if (catalogNeedsSecrets(item)) {
      secretsItem.value = item
      secretsOpen.value = true
      return
    }
    await install(item)
  }

  const submitSecrets = async (headers: VariableItem[]) => {
    const item = secretsItem.value
    if (!item) return
    const ok = await install(item, headers)
    if (!ok) return
    secretsOpen.value = false
    secretsItem.value = null
  }

  return {
    connect,
    isInstalled,
    installingUid,
    secretsItem,
    secretsOpen,
    submitSecrets,
  }
}
