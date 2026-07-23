import { apiClient } from './apiClient'
import type { ApplyWorkflowActionRequest, ApplyWorkflowActionResponse, PendingApprovalsResponse, WorkflowActionPreviewRequest, WorkflowActionPreviewResponse, WorkflowDocumentDetail } from '../types/workflow'

export const workflowService = {
  listPending(doctype?: string): Promise<PendingApprovalsResponse> {
    const query = doctype ? `?doctype=${encodeURIComponent(doctype)}` : ''
    return apiClient.get(`/api/workflow/pending${query}`)
  },
  getDocument(doctype: string, name: string): Promise<WorkflowDocumentDetail> {
    return apiClient.get(`/api/workflow/document/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`)
  },
  previewAction(payload: WorkflowActionPreviewRequest): Promise<WorkflowActionPreviewResponse> {
    return apiClient.post('/api/workflow/action-preview', payload)
  },
  applyAction(payload: ApplyWorkflowActionRequest): Promise<ApplyWorkflowActionResponse> {
    return apiClient.post('/api/workflow/apply-action', payload)
  },
}
