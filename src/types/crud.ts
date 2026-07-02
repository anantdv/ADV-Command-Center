export type MissingField = {
  fieldname: string
  label: string
  fieldtype: string
  options?: string | null
  required: boolean
}

export type ContinueCrudRequest = {
  operation: 'create' | 'update'
  doctype: string
  record_name?: string | null
  data: Record<string, unknown>
  conversation_id?: string | null
  message_id?: string | null
}

export type ConfirmCrudResponse = {
  operation: 'create' | 'update'
  doctype: string
  record_name: string
  status?: string | null
  message: string
  data?: Record<string, unknown> | null
}

export type CancelCrudResponse = { cancelled: boolean }
