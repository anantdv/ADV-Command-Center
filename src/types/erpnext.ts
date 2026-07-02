import type { PermissionMeta } from './api'

export interface ErpnextUserContext { user: string; fullName: string; company?: string; companyCurrency?: string; allowedCompanies?: string[]; timezone?:string; roles: string[]; permissions: PermissionMeta }
export interface AllowedDoctype { name: string; label: string; module: string; permissions: PermissionMeta }
export interface DoctypeSchemaRequest { doctype: string }
export interface DoctypeSchemaResponse { doctype: string; fields: Array<{ fieldname: string; label: string; fieldtype: string; required?: boolean }>; permissions: PermissionMeta }
export interface ListRecordsRequest { doctype: string; fields?: string[]; filters?: unknown[]; limitStart?: number; limitPageLength?: number; orderBy?: string }
export interface ListRecordsResponse { records: Array<Record<string, unknown>>; total: number; permissions: PermissionMeta }
export interface GetRecordRequest { doctype: string; name: string }
export interface RecordMutationRequest { doctype: string; name?: string; values: Record<string, unknown>; confirmed?: boolean }
export interface RecordResponse { record: Record<string, unknown>; permissions: PermissionMeta }
