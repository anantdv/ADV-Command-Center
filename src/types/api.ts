export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface ApiErrorShape {
  status: number
  message: string
  details?: unknown
}

export interface PermissionMeta {
  canRead: boolean
  canWrite: boolean
  canCreate: boolean
  canDelete: boolean
  canSubmit?: boolean
  canCancel?: boolean
  canExport?: boolean
  reason?: string
}
