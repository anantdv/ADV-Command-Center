import type { PermissionMeta } from './api'

export type FileItem = { id: string; name: string; type: string; generatedBy: string; module: string; date: string; permission: 'Private' | 'Team' | 'Company'; permissions?: PermissionMeta }
export type LibraryFilesResponse = FileItem[]
export type CreateLibraryFileRequest = { name: string; type: string; module: string; sourceId?: string }
