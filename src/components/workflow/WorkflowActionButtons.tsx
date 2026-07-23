import { useState } from 'react'
import { GitBranch, Loader2 } from 'lucide-react'
import { workflowService } from '../../services/workflowService'
import type { ApplyWorkflowActionResponse, WorkflowAction, WorkflowActionPreviewResponse } from '../../types/workflow'
import { WorkflowActionConfirmDialog } from './WorkflowActionConfirmDialog'

type Props = {
  doctype: string
  name: string
  actions: WorkflowAction[]
  onApplied?: (response: ApplyWorkflowActionResponse) => void
}

export function WorkflowActionButtons({ doctype, name, actions, onApplied }: Props) {
  const [busyAction, setBusyAction] = useState<string | null>(null)
  const [preview, setPreview] = useState<WorkflowActionPreviewResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  if (!actions.length) return null
  async function previewAction(action: WorkflowAction) {
    setBusyAction(action.action); setError(null)
    try {
      setPreview(await workflowService.previewAction({ doctype, name, action: action.action }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not prepare workflow confirmation.')
    } finally { setBusyAction(null) }
  }
  return <div className="space-y-2">
    <div className="flex flex-wrap gap-2">
      {actions.map(action => <button key={action.action} type="button" onClick={() => void previewAction(action)} disabled={Boolean(busyAction)} className="btn-secondary h-8 px-3 text-xs">
        {busyAction === action.action ? <Loader2 size={13} className="animate-spin"/> : <GitBranch size={13}/>}
        {action.label || action.action}
      </button>)}
    </div>
    {error && <div className="rounded-xl border border-red-200 bg-red-50 p-2 text-[11px] font-semibold text-red-700">{error}</div>}
    <WorkflowActionConfirmDialog preview={preview} onClose={() => setPreview(null)} onApplied={onApplied}/>
  </div>
}
