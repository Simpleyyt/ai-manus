import type { Component } from 'vue';
import { useI18n } from 'vue-i18n';
import FileIcon from '../components/icons/FileIcon.vue';
import CodeFileIcon from '../components/icons/CodeFileIcon.vue';
import UnknownFilePreview from '../components/filePreviews/UnknownFilePreview.vue';
import MarkdownFilePreview from '../components/filePreviews/MarkdownFilePreview.vue';
import CodeFilePreview from '../components/filePreviews/CodeFilePreview.vue';
import ImageFilePreview from '../components/filePreviews/ImageFilePreview.vue';

export interface FileType {
  icon: Component;
  preview: Component;
}

const codeFileExtensions = [
  'py', 'js', 'ts', 'jsx', 'tsx', 'vue',
  'java', 'c', 'cpp', 'h', 'hpp',
  'go', 'rust', 'php', 'ruby', 'swift',
  'kotlin', 'scala', 'haskell', 'erlang', 'elixir',
  'ocaml', 'fsharp', 'dart', 'julia',
  'lua', 'perl', 'r', 'sh', 'bash',
  'css', 'scss', 'sass', 'less', 'txt',
  'html', 'xml', 'json', 'yaml', 'yml',
  'sql', 'dockerfile', 'toml', 'ini', 'conf',
];

const imageFileExtensions = [
  'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff', 'tif', 'heic', 'heif',
];

const documentFileExtensions = [
  'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp',
];

const videoFileExtensions = [
  'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', '3gp', 'ogv',
];

const audioFileExtensions = [
  'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus',
];

const archiveFileExtensions = [
  'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'lzma',
];

export const getFileType = (filename: string): FileType => {
  const file_extension = filename.split('.').pop()?.toLowerCase();
  
  if (file_extension === 'md') {
    return {
      icon: FileIcon,
      preview: MarkdownFilePreview,
    };
  }
  
  if (file_extension && codeFileExtensions.includes(file_extension)) {
    return {
      icon: CodeFileIcon,
      preview: CodeFilePreview,
    };
  }

  if (file_extension && imageFileExtensions.includes(file_extension)) {
    return {
      icon: FileIcon,
      preview: ImageFilePreview,
    };
  }
  
  return {
    icon: FileIcon,
    preview: UnknownFilePreview,
  };
};

/**
 * Get file type text based on file extension
 * @param filename - The filename to analyze
 * @returns Localized description of file type
 */
export const getFileTypeText = (filename: string): string => {
  const { t } = useI18n();
  const file_extension = filename.split('.').pop()?.toLowerCase();
  
  if (!file_extension) {
    return t('File');
  }

  // Text files
  if (file_extension === 'txt') {
    return t('Text');
  }

  // Markdown files
  if (file_extension === 'md') {
    return t('Markdown');
  }

  // Code files
  if (codeFileExtensions.includes(file_extension)) {
    return t('Code');
  }

  // Image files
  if (imageFileExtensions.includes(file_extension)) {
    return t('Image');
  }

  // Document files
  if (file_extension === 'pdf') {
    return t('PDF');
  }
  if (['doc', 'docx'].includes(file_extension)) {
    return t('Word');
  }
  if (['xls', 'xlsx'].includes(file_extension)) {
    return t('Excel');
  }
  if (['ppt', 'pptx'].includes(file_extension)) {
    return t('PowerPoint');
  }
  if (documentFileExtensions.includes(file_extension)) {
    return t('Document');
  }

  // Video files
  if (videoFileExtensions.includes(file_extension)) {
    return t('Video');
  }

  // Audio files
  if (audioFileExtensions.includes(file_extension)) {
    return t('Audio');
  }

  // Archive files
  if (archiveFileExtensions.includes(file_extension)) {
    return t('Archive');
  }

  // Default
  return t('File');
};

/**
 * Format file size from bytes to human readable format
 * @param bytes - File size in bytes
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted file size string
 */
export function formatFileSize(bytes: number, decimals: number = 1): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
} 