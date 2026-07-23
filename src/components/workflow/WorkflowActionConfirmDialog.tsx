import { useState } from 'react'
import { CheckCircle2, Loader2, X } from 'lucide-react'
import { workflowService } from '../../services/workflowService'
import type { ApplyWorkflowActionResponse, WorkflowActionPreviewResponse } from '../../types/workflow'

type Props = {
  preview: WorkflowActionPreviewResponse | null
  onClose: () => void
  onApplied?: (response: ApplyWorkflowActionResponse) => void
}

export function WorkflowActionConfirmDialog({ preview, onClose, onApplied }: Props) {
  const [comment, setComment] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  if (!preview) return null
  const confirmationId = preview.confirmationId || preview.confirmation_id || ''
  const currentState = preview.currentState || preview.current_state || 'Current'
  const nextState = preview.nextState || preview.next_state || 'Next'
  async function confirm() {
    setBusy(true); setError(null)
    try {
      const response = await workflowService.applyAction({ doctype: preview!.doctype, name: preview!.name, action: preview!.action, comment: comment || undefined, confirmation_id: confirmationId })
      onApplied?.(response)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not apply workflow action.')
    } finally { setBusy(false) }
  }
  return <div className="fixed inset-0 z-[70] grid place-items-center bg-slate-950/40 p-4">
    <div className="w-full max-w-lg rounded-2xl bg-white p-5 shadow-2xl">
      <div className="flex items-start justify-between gap-3 border-b pb-4">
        <div><p className="text-xs font-bold uppercase tracking-wider text-amber-500">Workflow confirmation</p><h2 className="mt-1 text-lg font-bold text-slate-900">{preview.action}</h2><p className="mt-1 text-xs text-slate-500">{preview.doctype} · {preview.name}</p></div>
        <button className="rounded-lg p-2 hover:bg-slate-100" onClick={onClose}><X size={17}/></button>
      </div>
      <div className="mt-4 rounded-xl border bg-slate-50 p-3 text-sm">
        <p className="font-bold text-slate-800">{preview.title || preview.name}</p>
        <p className="mt-1 text-xs text-slate-500">State: {currentState} → {nextState}</p>
        {!!preview.summary && <div className="mt-3 grid gap-2 sm:grid-cols-2">{Object.entries(preview.summary).slice(0, 6).map(([key, value]) => <div key={key} className="rounded-lg bg-white px-3 py-2"><p className="text-[10px] font-bold uppercase text-slate-400">{label(key)}</p><p className="truncate text-xs font-semibold text-slate-700">{String(value ?? '—')}</p></div>)}</div>}
      </div>
      <label className="mt-4 block text-xs font-bold text-slate-600">Comment optional</label>
      <textarea value={comment} onChange={event => setComment(event.target.value)} className="mt-2 min-h-20 w-full rounded-xl border p-3 text-sm outline-none focus:border-indigo-300" placeholder="Add a review note for ERPNext..." />
      {error && <div className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-xs font-semibold text-red-700">{error}</div>}
      <div className="mt-5 flex justify-end gap-2">
        <button className="btn-secondary" onClick={onClose} disabled={busy}>Cancel</button>
        <button className="btn-primary" onClick={() => void confirm()} disabled={busy || !confirmationId}>{busy ? <Loader2 size={15} className="animate-spin"/> : <CheckCircle2 size={15}/>}Confirm {preview.action}</button>
      </div>
    </div>
  </div>
}

function label(key: string) { return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) }
