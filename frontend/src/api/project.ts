import { apiClient, ApiResponse } from './client';
import { ListProjectsResponse, ProjectItem, LibraryResponse } from '../types/response';

export async function getProjects(): Promise<ListProjectsResponse> {
  const response = await apiClient.get<ApiResponse<ListProjectsResponse>>('/projects');
  return response.data.data;
}

export async function getProject(projectId: string): Promise<ProjectItem> {
  const response = await apiClient.get<ApiResponse<ProjectItem>>(`/projects/${projectId}`);
  return response.data.data;
}

export async function createProject(name: string, instruction?: string): Promise<ProjectItem> {
  const response = await apiClient.post<ApiResponse<ProjectItem>>('/projects', { name, instruction });
  return response.data.data;
}

export async function updateProject(
  projectId: string,
  data: { name?: string; instruction?: string }
): Promise<ProjectItem> {
  const response = await apiClient.patch<ApiResponse<ProjectItem>>(`/projects/${projectId}`, data);
  return response.data.data;
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiClient.delete<ApiResponse<void>>(`/projects/${projectId}`);
}

export async function pinProject(projectId: string, isPinned: boolean): Promise<ProjectItem> {
  const response = await apiClient.post<ApiResponse<ProjectItem>>(`/projects/${projectId}/pin`, {
    is_pinned: isPinned,
  });
  return response.data.data;
}

export async function getLibraryFiles(): Promise<LibraryResponse> {
  const response = await apiClient.get<ApiResponse<LibraryResponse>>('/library/files');
  return response.data.data;
}

export async function favoriteLibraryFile(
  fileId: string
): Promise<{ file_id: string; is_favorite: boolean }> {
  const response = await apiClient.post<ApiResponse<{ file_id: string; is_favorite: boolean }>>(
    `/library/files/${fileId}/favorite`
  );
  return response.data.data;
}

export async function unfavoriteLibraryFile(
  fileId: string
): Promise<{ file_id: string; is_favorite: boolean }> {
  const response = await apiClient.delete<ApiResponse<{ file_id: string; is_favorite: boolean }>>(
    `/library/files/${fileId}/favorite`
  );
  return response.data.data;
}
