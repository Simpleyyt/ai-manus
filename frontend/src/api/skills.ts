import { apiClient, ApiResponse } from './client'
import type { Skill } from '../types/skill'

export type AddedSkill = Skill & { enabled: boolean }

export type SkillsStateResponse = {
  catalog: Skill[]
  added: AddedSkill[]
}

export async function fetchSkillsState(): Promise<SkillsStateResponse> {
  const response = await apiClient.get<ApiResponse<SkillsStateResponse>>('/skills')
  return response.data.data
}

export async function addSkills(skillIds: string[]): Promise<SkillsStateResponse> {
  const response = await apiClient.post<ApiResponse<SkillsStateResponse>>('/skills/added', {
    skill_ids: skillIds,
  })
  return response.data.data
}

export async function setSkillEnabled(skillId: string, enabled: boolean): Promise<AddedSkill> {
  const response = await apiClient.patch<ApiResponse<AddedSkill>>(`/skills/added/${skillId}`, {
    enabled,
  })
  return response.data.data
}

export async function importSkillFromGitHub(url: string): Promise<AddedSkill> {
  const response = await apiClient.post<ApiResponse<{ skill: AddedSkill }>>('/skills/import/github', {
    url,
  })
  return response.data.data.skill
}

export async function importSkillFromUpload(file: File): Promise<AddedSkill> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await apiClient.post<ApiResponse<{ skill: AddedSkill }>>(
    '/skills/import/upload',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    },
  )
  return response.data.data.skill
}
