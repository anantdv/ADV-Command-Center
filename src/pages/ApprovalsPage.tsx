import { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, ClipboardCheck, ExternalLink, RefreshCw, RotateCcw, XCircle } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { workflowService } from '../services/workflowService'
import type { ApplyWorkflowActionResponse, PendingWorkflowDocument, WorkflowAction, WorkflowActionPreviewResponse, WorkflowDocumentDetail } from '../types/workflow'
import { cn } from '../utils/cn'
import { WorkflowActionConfirmDialog } from '../components/workflow/WorkflowActionConfirmDialog'

const preferredDoctypes = ['Purchase Order', 'Purchase Invoice', 'Expense Claim', 'Leave Application', 'Sales Order']

export function ApprovalsPage() {
  const [documents, setDocuments] = useState<PendingWorkflowDocument[]>([])
  const [selected, setSelected] = useState<PendingWorkflowDocument | null>(null)
  const [detail, setDetail] = useState<WorkflowDocumentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [actioning, setActioning] = useState<string | null>(null)
  const [preview, setPreview] = useState<WorkflowActionPreviewResponse | null>(null)

  async function load() {
    setLoading(true); setError(null)
    try {
      const response = await workflowService.listPending()
      setDocuments(response.documents || [])
      setSelected(current => current && response.documents.some(doc => sameDoc(doc, current)) ? current : response.documents[0] || null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load pending approvals.')
    } finally { setLoading(false) }
  }

  useEffect(() => { void load() }, [])

  useEffect(() => {
    if (!selected) { setDetail(null); return }
    setDetailLoading(true)
    workflowService.getDocument(selected.doctype, selected.name)
      .then(setDetail)
      .catch(err => setError(err instanceof Error ? err.message : 'Could not load approval document.'))
      .finally(() => setDetailLoading(false))
  }, [selected])

  const grouped = useMemo(() => groupByDoctype(documents), [documents])
  const orderedGroups = useMemo(() => Object.keys(grouped).sort((a, b) => {
    const ai = preferredDoctypes.indexOf(a); const bi = preferredDoctypes.indexOf(b)
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi) || a.localeCompare(b)
  }), [grouped])

  async function apply(action: WorkflowAction) {
    if (!selected) return
    setActioning(action.action)
    try {
      setPreview(await workflowService.previewAction({ doctype: selected.doctype, name: selected.name, action: action.action }))
    } catch (err) {
      setError(err instanceof Error ? err.message : `Could not prepare ${action.action}.`)
    } finally { setActioning(null) }
  }

  async function afterApplied(_response: ApplyWorkflowActionResponse) {
    setPreview(null)
    await load()
  }

  if (loading) return <LoadingState table />
  if (error && !documents.length) return <ErrorState message={error} retry={() => void load()} />

  return <div className="space-y-5">
    <PageHeader eyebrow="ERPNext Workflow Inbox" title="Approvals" description="Review documents waiting for your ERPNext workflow action. Actions are executed by ERPNext workflow only." actions={<button className="btn-secondary" onClick={() => void load()}><RefreshCw size={15}/>Refresh</button>} />
    {error && <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">{error}</div>}
    {!documents.length ? <EmptyState title="No pending approvals." description="There are no ERPNext Workflow Action documents currently actionable for your session." action={<div className="flex flex-wrap justify-center gap-2"><button className="btn-secondary" onClick={() => void load()}>Refresh</button><a className="btn-secondary" href="/app/workflow-action" target="_blank" rel="noreferrer">Open ERPNext Workflow</a><a className="btn-secondary" href="/modules/buying/doctype/Purchase%20Order">Show Purchase Orders</a><a className="btn-secondary" href="/modules/accounts/doctype/Purchase%20Invoice">Show Purchase Invoices</a></div>} /> : <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
      <section className="card overflow-hidden">
        <div className="border-b p-4">
          <div className="flex items-center gap-2 text-sm font-bold"><ClipboardCheck size={17} className="text-purple-600"/>Pending approval inbox</div>
          <p className="mt-1 text-xs text-slate-500">{documents.length} document{documents.length === 1 ? '' : 's'} waiting for action</p>
        </div>
        <div className="max-h-[70vh] overflow-y-auto p-3">
          {orderedGroups.map(doctype => <div key={doctype} className="mb-4">
            <div className="mb-2 flex items-center justify-between px-1 text-[10px] font-bold uppercase tracking-wider text-slate-400"><span>{doctype}</span><span>{grouped[doctype].length}</span></div>
            <div className="space-y-2">{grouped[doctype].map(doc => <button key={`${doc.doctype}:${doc.name}`} onClick={() => setSelected(doc)} className={cn('w-full rounded-2xl border p-3 text-left transition hover:border-purple-200 hover:bg-purple-50/40', selected && sameDoc(doc, selected) ? 'border-purple-300 bg-purple-50 ring-2 ring-purple-100' : 'border-slate-200 bg-white')}>
              <div className="flex items-start justify-between gap-3">
                <div><p className="text-xs font-bold text-slate-800">{doc.title || doc.name}</p><p className="mt-1 text-[11px] text-slate-500">{party(doc) || doc.status || 'Pending workflow action'}</p></div>
                <span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-700">{state(doc)}</span>
              </div>
              <div className="mt-2 flex justify-between text-[11px] text-slate-400"><span>{dateOf(doc) || 'No date'}</span><span>{money(doc)}</span></div>
            </button>)}</div>
          </div>)}
        </div>
      </section>
      <section className="card min-h-[520px] p-5">
        {detailLoading ? <LoadingState /> : detail ? <ApprovalDetail detail={detail} actioning={actioning} onApply={apply} /> : <EmptyState title="Select an approval" description="Choose a document from the inbox to review summary, workflow history, comments, attachments, and actions." />}
      </section>
    </div>}
    <WorkflowActionConfirmDialog preview={preview} onClose={() => setPreview(null)} onApplied={response => void afterApplied(response)}/>
  </div>
}

function ApprovalDetail({ detail, actioning, onApply }: { detail: WorkflowDocumentDetail; actioning: string | null; onApply: (action: WorkflowAction) => void }) {
  const actions = detail.availableActions || detail.available_actions || []
  const summary = detail.summary || {}
  return <div className="space-y-5">
    <div className="flex flex-col gap-3 border-b pb-5 md:flex-row md:items-start md:justify-between">
      <div><p className="text-xs font-bold uppercase tracking-wider text-purple-500">{detail.doctype}</p><h2 className="mt-1 text-2xl font-bold text-slate-900">{detail.title || detail.name}</h2><p className="mt-1 text-sm text-slate-500">{detail.workflowState || detail.workflow_state || detail.status || 'Pending workflow action'}</p></div>
      <a className="btn-secondary" href={`/app/${detail.doctype.toLowerCase().replaceAll(' ', '-')}/${detail.name}`} target="_blank" rel="noreferrer"><ExternalLink size={15}/>Open in ERPNext</a>
    </div>
    <div className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-violet-50 p-4">
      <p className="text-xs font-bold uppercase tracking-wider text-indigo-500">AI summary</p>
      <p className="mt-2 text-sm leading-6 text-slate-700">{executiveSummary(detail)}</p>
    </div>
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {Object.entries(summary).slice(0, 9).map(([key, value]) => <div key={key} className="rounded-2xl border bg-white p-4">
        <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{label(key)}</p>
        <p className="mt-1 break-words text-sm font-bold text-slate-800">{String(value ?? '—')}</p>
      </div>)}
    </div>
    {!!detail.items?.length && <div className="overflow-hidden rounded-2xl border">
      <div className="border-b bg-slate-50 px-4 py-3 text-xs font-bold">Items</div>
      <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-xs"><thead><tr className="border-b">{Object.keys(detail.items[0]).slice(0, 8).map(key => <th key={key} className="px-4 py-3 text-slate-400">{label(key)}</th>)}</tr></thead><tbody>{detail.items.slice(0, 20).map((row, idx) => <tr key={idx} className="border-b">{Object.keys(detail.items[0]).slice(0, 8).map(key => <td key={key} className="px-4 py-3">{String(row[key] ?? '')}</td>)}</tr>)}</tbody></table></div>
    </div>}
    <div className="rounded-2xl border p-4">
      <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Workflow actions</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {actions.length ? actions.map(action => <button key={action.action} disabled={!!actioning} onClick={() => onApply(action)} className={cn('btn-secondary', action.action.toLowerCase().includes('approve') && 'border-emerald-200 bg-emerald-50 text-emerald-700', action.action.toLowerCase().includes('reject') && 'border-red-200 bg-red-50 text-red-700')}>
          {action.action.toLowerCase().includes('approve') ? <CheckCircle2 size={15}/> : action.action.toLowerCase().includes('reject') ? <XCircle size={15}/> : <RotateCcw size={15}/>}
          {actioning === action.action ? 'Applying...' : action.action}
        </button>) : <p className="text-sm text-slate-500">No workflow actions are currently available for your user.</p>}
      </div>
    </div>
  </div>
}

function groupByDoctype(docs: PendingWorkflowDocument[]) { return docs.reduce<Record<string, PendingWorkflowDocument[]>>((acc, doc) => { (acc[doc.doctype] ||= []).push(doc); return acc }, {}) }
function sameDoc(a: PendingWorkflowDocument, b: PendingWorkflowDocument) { return a.doctype === b.doctype && a.name === b.name }
function state(doc: PendingWorkflowDocument) { return doc.workflowState || doc.workflow_state || doc.status || 'Pending' }
function party(doc: PendingWorkflowDocument) { return doc.party }
function dateOf(doc: PendingWorkflowDocument) { return doc.postingDate || doc.posting_date || doc.transactionDate || doc.transaction_date || doc.modified }
function money(doc: PendingWorkflowDocument) { const total = doc.grandTotal ?? doc.grand_total; return total == null ? '' : `${doc.currency || ''} ${Number(total).toLocaleString()}`.trim() }
function label(key: string) { return key.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/\b\w/g, c => c.toUpperCase()) }
function executiveSummary(detail: WorkflowDocumentDetail) {
  const total = detail.summary?.grand_total || detail.summary?.grandTotal
  const currency = detail.summary?.currency
  const party = detail.summary?.supplier || detail.summary?.customer || detail.summary?.party || detail.summary?.party_name
  const state = detail.workflowState || detail.workflow_state || detail.status || 'pending review'
  return `${detail.doctype} ${detail.name} is ${state}. ${party ? `Party: ${party}. ` : ''}${total ? `Total: ${currency || ''} ${Number(total).toLocaleString()}. ` : ''}Review the document details and choose an available ERPNext workflow action when ready.`
}
