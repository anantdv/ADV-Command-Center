export type SuggestionType = 'prompt' | 'action' | 'navigation' | 'export' | 'pin' | 'workflow_action' | 'crud_confirmation'
export type SuggestionRisk = 'low' | 'medium' | 'high'

export interface SuggestedPrompt {
  id: string
  label: string
  type: SuggestionType
  prompt?: string | null
  actionType?: string | null
  action_type?: string | null
  endpoint?: string | null
  payload?: Record<string, unknown>
  icon?: string | null
  risk: SuggestionRisk
  requiresConfirmation?: boolean
  requires_confirmation?: boolean
  disabled?: boolean
  disabledReason?: string | null
  disabled_reason?: string | null
  group?: string | null
}

export interface SuggestionContext {
  conversationId?: string | null
  messageId?: string | null
  previousPrompt?: string | null
  resultType?: string
  doctype?: string | null
  sourceName?: string | null
  rowCount?: number | null
}

export interface SuggestionResponse {
  suggestions: SuggestedPrompt[]
}
