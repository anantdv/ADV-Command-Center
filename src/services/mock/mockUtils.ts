import type { PermissionMeta } from '../../types/api'

export const mockDelay = async <T>(value: T, ms = 180): Promise<T> => { await new Promise(resolve => setTimeout(resolve, ms)); return value }
export const fullPermission: PermissionMeta = { canRead: true, canWrite: true, canCreate: true, canDelete: false, canSubmit: true, canCancel: false, canExport: true }
export const readOnlyPermission: PermissionMeta = { canRead: true, canWrite: false, canCreate: false, canDelete: false, canExport: true, reason: 'Your ERPNext role provides read-only access.' }
