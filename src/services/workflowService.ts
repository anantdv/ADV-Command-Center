import { apiClient } from './apiClient'
import type { ApplyWorkflowActionRequest, ApplyWorkflowActionResponse, PendingApprovalsResponse, WorkflowDocumentDetail } from '../types/workflow'

export const workflowService = {
  listPending(doctype?: string): Promise<PendingApprovalsResponse> {
    const query = doctype ? `?doctype=${encodeURIComponent(doctype)}` : ''
    return apiClient.get(`/api/workflow/pending${query}`)
  },
  getDocument(doctype: string, name: string): Promise<WorkflowDocumentDetail> {
    return apiClient.get(`/api/workflow/document/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`)
  },
  applyAction(payload: ApplyWorkflowActionRequest): Promise<ApplyWorkflowActionResponse> {
    return apiClient.post('/api/workflow/action', payload)
  },
}
