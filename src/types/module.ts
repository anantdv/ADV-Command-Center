import type { LucideIcon } from 'lucide-react'
import type { PermissionMeta } from './api'

export type Module = { slug: string; name: string; description: string; metric: string; metricLabel: string; icon: LucideIcon; color: string; permissions?: PermissionMeta }
export type ModuleDetailData = { module: Module; records: string[]; reports?: string[] }
export type ModuleListResponse = Module[]
export type ModuleDetailResponse = ModuleDetailData
export type ModuleRecordsResponse = { records: Array<Record<string, unknown>>; permissions: PermissionMeta }
export type ModuleReportsResponse = { reports: string[]; permissions: PermissionMeta }
