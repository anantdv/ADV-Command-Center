import type { LucideIcon } from 'lucide-react'
import type { PermissionMeta } from './api'

export type Module = { slug: string; name: string; description: string; metric: string; metricLabel: string; icon: LucideIcon; color: string; permissions?: PermissionMeta }
export type ModuleDetailData = { module: Module; records: string[]; reports?: string[] }
export type ModuleListResponse = Module[]
export type ModuleDetailResponse = ModuleDetailData
export type ModuleRecordsResponse = { records: Array<Record<string, unknown>>; permissions: PermissionMeta }
export type ModuleReportsResponse = { reports: string[]; permissions: PermissionMeta }
export type ModuleKpi = { id:string; label:string; value:number|string; valueType:'number'|'currency'|'percent'|'text'; currency?:string|null; trendLabel?:string|null; trendValue?:number|null; sourceDoctype?:string|null; filters?:Record<string,unknown>; actionPrompt?:string|null }
export type ModuleReport = { id:string; title:string; description?:string|null; reportType:'table'|'chart'|'standard_report'|'analytics'; sourceDoctype?:string|null; reportName?:string|null; chartType?:string|null; data:Array<Record<string,unknown>>; columns:Array<{key:string;label:string}>; actionPrompt?:string|null }
export type ModuleRecentDocument = { doctype:string; name:string; title?:string|null; status?:string|null; workflowState?:string|null; party?:string|null; amount?:number|null; currency?:string|null; date?:string|null; modified?:string|null }
export type ModuleQuickAction = { id:string; label:string; prompt:string; enabled?:boolean; doctype?:string }
export type ModuleDashboard = { moduleName:string; label:string; kpis:ModuleKpi[]; reports:ModuleReport[]; recentDocuments:ModuleRecentDocument[]; quickActions:ModuleQuickAction[]; permissions:Record<string,unknown>; doctypes:string[]; pinnedWidgets?:Array<Record<string,unknown>> }
export type ModuleDoctypeInfo={doctype:string;label:string;description?:string|null;icon?:string|null;canRead:boolean;canCreate:boolean;recordCount?:number|null;route:string;defaultFields:string[]}
export type ModuleDoctypeNavigation={moduleName:string;doctypes:ModuleDoctypeInfo[]}
export type ModuleDoctypeRecords={moduleName:string;doctype:string;page:number;pageSize:number;total:number;columns:Array<{key:string;label:string}>;rows:Array<Record<string,unknown>>}
