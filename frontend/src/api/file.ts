// File API service
import { apiClient, ApiResponse } from './client';

/**
 * File upload result type
 */
export interface FileUploadResult {
  file_id: string;
  filename: string;
  content_type?: string;
  size: number;
  upload_time: string;
  metadata?: Record<string, any>;
}

/**
 * File download result type  
 */
export interface FileDownloadResult {
  file_id: string;
  filename: string;
  content_type?: string;
  size: number;
  data: Blob;
}

/**
 * File info type
 */
export interface FileInfo {
  file_id: string;
  filename: string;
  content_type?: string;
  size: number;
  upload_time: string;
  metadata?: Record<string, any>;
}

/**
 * Upload file
 * @param file File to upload
 * @param metadata Optional metadata
 * @returns Upload result
 */
export async function uploadFile(file: File, metadata?: Record<string, any>): Promise<FileUploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  
  if (metadata) {
    formData.append('metadata', JSON.stringify(metadata));
  }

  const response = await apiClient.post<ApiResponse<FileUploadResult>>('/files', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data.data;
}

/**
 * Download file
 * @param fileId File ID
 * @returns File download result
 */
export async function downloadFile(fileId: string): Promise<FileDownloadResult> {
  const response = await apiClient.get(`/files/${fileId}/download`, {
    responseType: 'blob',
  });
  
  // Get file info from response headers
  const contentType = response.headers['content-type'];
  const contentDisposition = response.headers['content-disposition'];
  const filename = contentDisposition 
    ? contentDisposition.split('filename=')[1]?.replace(/"/g, '') 
    : 'download';
  
  return {
    file_id: fileId,
    filename: filename || 'download',
    content_type: contentType,
    size: response.data.size || 0,
    data: response.data
  };
}

/**
 * Delete file
 * @param fileId File ID
 * @returns Success status
 */
export async function deleteFile(fileId: string): Promise<boolean> {
  try {
    await apiClient.delete<ApiResponse<void>>(`/files/${fileId}`);
    return true;
  } catch (error) {
    console.error('Failed to delete file:', error);
    return false;
  }
}

/**
 * Get file information
 * @param fileId File ID
 * @returns File information or null if not found
 */
export async function getFileInfo(fileId: string): Promise<FileInfo | null> {
  try {
    const response = await apiClient.get<ApiResponse<FileInfo>>(`/files/${fileId}`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to get file info:', error);
    return null;
  }
}

/**
 * Get file download URL
 * @param fileId File ID
 * @returns Download URL string
 */
export function getFileDownloadUrl(fileId: string): string {
  return `${apiClient.defaults.baseURL}/files/${fileId}`;
}
