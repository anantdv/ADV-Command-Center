export type ChatRole = 'user' | 'assistant' | 'system' | 'tool'
import type { SuggestedPrompt } from './suggestions'
import type { AppDateRange } from './dateRange'
import type { DocumentMappingPreview } from './documentIntake'

export type SourceMeta = {
  source_type: 'doctype' | 'report' | 'tool'
  source_name: string
  record_count?: number | null
  filters?: Record<string, unknown> | null
  doctype?: string | null
  report_name?: string | null
  fields?: string[] | null
}

export type ChatPermissionMeta = {
  allowed: boolean
  risk_level: 'low' | 'medium' | 'high'
  confirmation_required: boolean
  filtered_fields: string[]
  blocked_fields: string[]
  reason?: string | null
}

export type TableColumn = { key: string; label: string; type: string }
export type TextPart = { type: 'text'; content: string }
export type ToolCallPart = {
  type: 'tool_call'
  tool_name?: string
  toolName?: string
  status: 'running' | 'success' | 'error'
  input_summary?: string | null
  output_summary?: string | null
}
export type TablePart = {
  type: 'table'
  result_id?: string | null
  resultId?: string | null
  title: string
  columns: TableColumn[]
  rows: Array<Record<string, unknown>>
  total_rows?: number | null
  config?: Record<string, unknown>
  row_action?: { type?: string; endpoint?: string } | null
}
export type ChartPart = {
  type: 'chart'
  result_id?: string | null
  resultId?: string | null
  source_type?: string | null
  sourceType?: string | null
  source_name?: string | null
  sourceName?: string | null
  module?: string | null
  title?: string
  chart_type?: 'bar' | 'line' | 'pie' | 'donut' | 'area'
  data?: Array<Record<string, unknown>>
  x_key?: string | null
  y_key?: string | null
  config?: Record<string, unknown>
  available_actions?: string[]
  chartConfig?: unknown
}
export type FilePart = { type: 'file'; fileId: string; fileName: string; fileType: string; fileFormat?: string; downloadUrl?: string; file_id?: string; file_name?: string; file_type?: string; file_format?: string; mime_type?: string; download_url?: string }
export type MissingFieldsPart = {
  type: 'missing_fields'
  doctype: string
  operation: 'create' | 'update'
  fields: import('./crud').MissingField[]
  collected_data: Record<string, unknown>
  record_name?: string | null
  conversation_id?: string | null
  message_id?: string | null
}
export type RecordPreviewPart = {
  type: 'record_preview'
  operation: 'create' | 'update'
  doctype: string
  record_name?: string | null
  before_data?: Record<string, unknown> | null
  after_data: Record<string, unknown>
  risk_level: 'medium' | 'high'
}
export type RecordDetailPart = {
  type: 'record_detail'
  doctype: string
  name: string
  title?: string | null
  status?: string | null
  workflow_state?: string | null
  docstatus?: number | null
  summary?: Record<string, unknown>
  fields?: Record<string, unknown>
  items?: Array<Record<string, unknown>>
  available_workflow_actions?: Array<Record<string, unknown>>
}
export type ConfirmationPart = {
  type: 'confirmation'
  confirmation_id: string
  title: string
  description: string
  confirm_label: string
  cancel_label: string
  risk_level: 'medium' | 'high'
}
export type OcrMappingPreviewPart = DocumentMappingPreview & { type: 'ocr_mapping_preview' }
export type ChatMessagePart = TextPart | ToolCallPart | TablePart | ChartPart | FilePart | MissingFieldsPart | RecordPreviewPart | RecordDetailPart | ConfirmationPart | OcrMappingPreviewPart

export type SuggestedAction = {
  label: string
  action_type: string
  disabled: boolean
  reason?: string | null
  payload?: Record<string, unknown>
}
export type ExtractionMeta = { method: 'vertex_gemini' | 'rules'; confidence?: number | null; provider?: string | null; model?: string | null; privacy_checked?: boolean; privacy_allowed?: boolean; erp_data_sent?: boolean; fallback_used?: boolean }

export interface ChatMessage {
  id: string
  conversationId: string
  role: ChatRole
  content: string
  createdAt: string
  parts?: ChatMessagePart[]
  intent?: string | null
  source?: SourceMeta | null
  permission?: ChatPermissionMeta | null
  suggestedActions?: SuggestedAction[]
  suggestions?: SuggestedPrompt[]
  extraction?: ExtractionMeta | null
}

export interface AssistantChatResponse {
  conversation_id: string
  message_id: string
  role: 'assistant'
  intent: string
  parts: ChatMessagePart[]
  source?: SourceMeta | null
  permission?: ChatPermissionMeta | null
  suggested_actions: SuggestedAction[]
  suggestions?: SuggestedPrompt[]
  extraction?: ExtractionMeta | null
  id: string
  content: string
  created_at: string
}

export interface Conversation { id: string; title: string; createdAt: string; updatedAt: string }
export interface CreateConversationRequest { title?: string }
export interface SendChatMessageRequest {
  conversation_id?: string
  message: string
  module_context?: string
  company?: string
  date_range?: { from_date: string; to_date: string }
  dateRange?: AppDateRange
  source?: string
  parent_message_id?: string
  active_report_id?: string
  active_result_id?: string
  current_filters?: Record<string, unknown>
  selected_rows?: Array<Record<string, unknown>>
  requested_output?: string
  structured_action?: Record<string, unknown>
}
export interface ChatActionResponse { actionId: string; status: 'confirmed' | 'cancelled' }
export type Invoice = { id: string; customer: string; due: string; days: number; amount: string; risk: string }
export type CommandCenterData = { invoices: Invoice[] }
