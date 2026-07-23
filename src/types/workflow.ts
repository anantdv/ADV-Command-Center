export type WorkflowAction = {
  action: string
  nextState?: string | null
  next_state?: string | null
  allowed?: boolean
  label?: string | null
}

export type PendingWorkflowDocument = {
  doctype: string
  name: string
  title?: string | null
  workflowState?: string | null
  workflow_state?: string | null
  status?: string | null
  owner?: string | null
  modified?: string | null
  postingDate?: string | null
  posting_date?: string | null
  transactionDate?: string | null
  transaction_date?: string | null
  party?: string | null
  grandTotal?: number | null
  grand_total?: number | null
  currency?: string | null
  availableActions?: WorkflowAction[]
  available_actions?: WorkflowAction[]
}

export type PendingApprovalsResponse = {
  documents: PendingWorkflowDocument[]
  total: number
  filters?: Record<string, unknown>
}

export type WorkflowDocumentDetail = {
  doctype: string
  name: string
  title?: string | null
  workflowState?: string | null
  workflow_state?: string | null
  status?: string | null
  docstatus?: number | null
  summary: Record<string, unknown>
  fields: Record<string, unknown>
  items: Array<Record<string, unknown>>
  availableActions?: WorkflowAction[]
  available_actions?: WorkflowAction[]
  permission?: Record<string, unknown> | null
}

export type ApplyWorkflowActionRequest = {
  doctype: string
  name: string
  action: string
  comment?: string
  confirmationId?: string
  confirmation_id?: string
}

export type ApplyWorkflowActionResponse = {
  doctype: string
  name: string
  action: string
  previousState?: string | null
  previous_state?: string | null
  newState?: string | null
  new_state?: string | null
  status?: string | null
  availableActions?: WorkflowAction[]
  available_actions?: WorkflowAction[]
  message: string
  result?: Record<string, unknown>
}

export type WorkflowActionPreviewRequest = {
  doctype: string
  name: string
  action: string
  comment?: string
}

export type WorkflowActionPreviewResponse = {
  doctype: string
  name: string
  action: string
  currentState?: string | null
  current_state?: string | null
  nextState?: string | null
  next_state?: string | null
  title?: string | null
  summary?: Record<string, unknown>
  confirmationRequired?: boolean
  confirmation_required?: boolean
  confirmationId?: string
  confirmation_id?: string
}
