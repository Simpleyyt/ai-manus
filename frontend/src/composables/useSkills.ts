import { onMounted } from 'vue'
import {
  addSkills,
  added,
  catalog,
  ensureSkillsLoaded,
  filterSkillsByQuery,
  getSkillById,
  importSkillFromGitHub,
  importSkillFromUpload,
  isSkillAdded,
  isSkillEnabled,
  launchSkillCreatorFlow,
  loadError,
  loaded,
  loading,
  officialCatalog,
  reloadSkills,
  setSkillEnabled,
  skills,
  slashSkills,
} from './skillsStore'

export function useSkills() {
  onMounted(() => {
    void ensureSkillsLoaded()
  })

  return {
    skills,
    slashSkills,
    catalog,
    officialCatalog,
    added,
    loading,
    loaded,
    loadError,
    filterByQuery: filterSkillsByQuery,
    isAdded: isSkillAdded,
    isEnabled: isSkillEnabled,
    getSkillById,
    addSkills,
    setSkillEnabled,
    importSkillFromGitHub,
    importSkillFromUpload,
    launchSkillCreatorFlow,
    reloadSkills,
    ensureSkillsLoaded,
  }
}
