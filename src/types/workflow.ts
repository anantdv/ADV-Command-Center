export type WorkflowAction = {
  action: string
  nextState?: string | null
  next_state?: string | null
  allowed?: boolean
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
  message: string
  result?: Record<string, unknown>
}
