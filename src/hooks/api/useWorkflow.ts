import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { workflowService } from '../../services/workflowService'

export const workflowKeys = {
  pending: ['workflow', 'pending'] as const,
  document: (doctype: string, name: string) => ['workflow', 'document', doctype, name] as const,
}

export const usePendingWorkflowApprovals = () => useQuery({ queryKey: workflowKeys.pending, queryFn: () => workflowService.listPending() })

export const useWorkflowDocument = (doctype: string, name: string) => useQuery({ queryKey: workflowKeys.document(doctype, name), queryFn: () => workflowService.getDocument(doctype, name), enabled: Boolean(doctype && name) })

export const useWorkflowActionPreview = () => useMutation({ mutationFn: workflowService.previewAction })

export function useApplyWorkflowAction() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: workflowService.applyAction,
    onSuccess: (_data, variables) => {
      void client.invalidateQueries({ queryKey: workflowKeys.pending })
      void client.invalidateQueries({ queryKey: workflowKeys.document(variables.doctype, variables.name) })
    },
  })
}
