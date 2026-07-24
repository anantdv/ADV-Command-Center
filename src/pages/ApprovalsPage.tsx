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
import { BusinessGraphPanel } from '../components/graph/BusinessGraphPanel'

const preferredDoctypes = ['Quotation', 'Sales Order', 'Purchase Order', 'Purchase Invoice', 'Expense Claim', 'Leave Application', 'Stock Entry', 'Journal Entry']

export function ApprovalsPage() {
  const [documents, setDocuments] = useState<PendingWorkflowDocument[]>([])
  const [selected, setSelected] = useState<PendingWorkflowDocument | null>(null)
  const [detail, setDetail] = useState<WorkflowDocumentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [actioning, setActioning] = useState<string | null>(null)
  const [preview, setPreview] = useState<WorkflowActionPreviewResponse | null>(null)

  async function load() {
    setLoading(true); setError(null)
    try {
      const response = await workflowService.listPending()
      setDocuments(response.documents || [])
      setSelected(current => current && response.documents.some(doc => sameDoc(doc, current)) ? current : null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load pending approvals.')
    } finally { setLoading(false) }
  }

  useEffect(() => { void load() }, [])

  useEffect(() => {
    if (!selected) { setDetail(null); setDetailError(null); return }
    setDetailLoading(true)
    setDetailError(null)
    workflowService.getDocument(selected.doctype, selected.name)
      .then(setDetail)
      .catch(err => {
        setDetail(null)
        setDetailError(err instanceof Error ? err.message : 'Could not load approval document.')
      })
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
    setDetail(null)
    setSelected(null)
    await load()
  }

  function removeSelectedFromQueue() {
    if (!selected) return
    setDocuments(current => current.filter(doc => !sameDoc(doc, selected)))
    setSelected(null)
    setDetail(null)
    setDetailError(null)
  }

  if (loading) return <LoadingState table />
  if (error && !documents.length) {
    const staleQueue = /not found/i.test(error)
    return staleQueue
      ? <StaleQueueError message={error} onRefresh={() => void load()} />
      : <ErrorState message={error} retry={() => void load()} />
  }

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
                <div className="min-w-0">
                  <div className="flex items-center gap-2"><span className={cn('size-2 shrink-0 rounded-full', unread(doc) ? 'bg-purple-500' : 'bg-slate-200')}/><p className="truncate text-xs font-bold text-slate-800">{doc.title || doc.name}</p></div>
                  <p className="mt-1 truncate text-[11px] text-slate-500">{party(doc) || doc.status || 'Pending workflow action'}</p>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1">
                  <span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-700">{state(doc)}</span>
                  <span className={priorityClass(priority(doc))}>{priority(doc)}</span>
                </div>
              </div>
              <div className="mt-2 grid gap-1 text-[11px] text-slate-400 sm:grid-cols-2">
                <span>{age(doc)}</span>
                <span className="sm:text-right">{money(doc)}</span>
                <span className="truncate sm:col-span-2">Requested by {requestedBy(doc)}</span>
              </div>
            </button>)}</div>
          </div>)}
        </div>
      </section>
      <section className="card min-h-[520px] p-5">
        {detailLoading ? <LoadingState /> : detail ? <ApprovalDetail detail={detail} actioning={actioning} onApply={apply} /> : detailError && selected ? <MissingApprovalDetail selected={selected} message={detailError} onRemove={removeSelectedFromQueue} onRefresh={() => void load()} /> : <EmptyState title="Select an approval from the left panel." description="The approval queue is the source of truth. Details load only after you choose a pending document." />}
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
        {actions.length ? actions.map(action => <button key={action.action} disabled={!!actioning} onClick={() => onApply(action)} className={workflowButtonClass(action.action)}>
          {actioning === action.action ? <RefreshCw size={15} className="animate-spin"/> : action.action.toLowerCase().includes('approve') ? <CheckCircle2 size={15}/> : action.action.toLowerCase().includes('reject') ? <XCircle size={15}/> : <RotateCcw size={15}/>}
          {actioning === action.action ? loadingLabel(action.action) : action.action}
        </button>) : <p className="text-sm text-slate-500">No workflow actions are currently available for your user.</p>}
      </div>
    </div>
    <div className="rounded-2xl border p-4">
      <p className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-400">Business graph</p>
      <BusinessGraphPanel doctype={detail.doctype} name={detail.name}/>
    </div>
  </div>
}

function MissingApprovalDetail({ selected, message, onRemove, onRefresh }: { selected: PendingWorkflowDocument; message: string; onRemove: () => void; onRefresh: () => void }) {
  return <div className="grid min-h-[480px] place-items-center text-center">
    <div className="max-w-md rounded-3xl border border-amber-200 bg-amber-50 p-6">
      <ClipboardCheck className="mx-auto text-amber-600" size={34}/>
      <h2 className="mt-3 text-lg font-bold text-slate-900">Document no longer exists.</h2>
      <p className="mt-2 text-sm text-slate-600">{selected.doctype} {selected.name} could not be loaded. It may have been deleted, completed, or you may no longer have access.</p>
      <p className="mt-2 rounded-xl bg-white/70 p-3 text-xs font-semibold text-amber-800">{message}</p>
      <div className="mt-5 flex flex-wrap justify-center gap-2">
        <button className="btn-secondary" onClick={onRemove}>Remove from queue</button>
        <button className="btn-primary" onClick={onRefresh}><RefreshCw size={14}/>Refresh</button>
      </div>
    </div>
  </div>
}

function StaleQueueError({ message, onRefresh }: { message: string; onRefresh: () => void }) {
  return <div className="grid min-h-[520px] place-items-center">
    <div className="max-w-xl rounded-3xl border border-amber-200 bg-white p-8 text-center shadow-sm">
      <ClipboardCheck className="mx-auto text-amber-600" size={38}/>
      <h2 className="mt-4 text-xl font-bold text-slate-900">Approval queue needs refresh</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">ERPNext has a stale Workflow Action pointing to a document that no longer exists. Refresh the queue after updating the companion app; valid approvals will continue to load.</p>
      <p className="mt-4 rounded-xl bg-amber-50 p-3 text-xs font-semibold text-amber-800">{message}</p>
      <div className="mt-5 flex flex-wrap justify-center gap-2">
        <button className="btn-primary" onClick={onRefresh}><RefreshCw size={14}/>Refresh queue</button>
        <a className="btn-secondary" href="/app/workflow-action" target="_blank" rel="noreferrer">Open ERPNext Workflow</a>
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
function requestedBy(doc: PendingWorkflowDocument) { const value = extra(doc, 'requested_by') || extra(doc, 'owner') || doc.owner; return String(value || 'ERPNext') }
function unread(doc: PendingWorkflowDocument) { return Boolean(extra(doc, 'unread') ?? extra(doc, 'is_unread')) }
function priority(doc: PendingWorkflowDocument) { return String(extra(doc, 'priority') || 'Normal') }
function age(doc: PendingWorkflowDocument) {
  const value = dateOf(doc)
  if (!value) return 'No date'
  const date = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return String(value)
  const days = Math.max(0, Math.floor((Date.now() - date.getTime()) / 86400000))
  if (days === 0) return 'Today'
  if (days === 1) return '1 day old'
  return `${days} days old`
}
function extra(doc: PendingWorkflowDocument, key: string) { return (doc as unknown as Record<string, unknown>)[key] }
function priorityClass(value: string) {
  const lower = value.toLowerCase()
  if (lower.includes('critical') || lower.includes('urgent')) return 'rounded-full bg-red-50 px-2 py-0.5 text-[9px] font-bold text-red-700'
  if (lower.includes('high')) return 'rounded-full bg-orange-50 px-2 py-0.5 text-[9px] font-bold text-orange-700'
  return 'rounded-full bg-slate-100 px-2 py-0.5 text-[9px] font-bold text-slate-500'
}
function label(key: string) { return key.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/\b\w/g, c => c.toUpperCase()) }
function workflowButtonClass(action: string) {
  const lower = action.toLowerCase()
  if (lower.includes('approve')) return 'inline-flex h-10 items-center gap-2 rounded-xl bg-[#16A34A] px-4 text-xs font-bold text-white shadow-sm transition hover:bg-[#15803D] disabled:cursor-not-allowed disabled:opacity-60'
  if (lower.includes('reject')) return 'inline-flex h-10 items-center gap-2 rounded-xl bg-[#DC2626] px-4 text-xs font-bold text-white shadow-sm transition hover:bg-[#B91C1C] disabled:cursor-not-allowed disabled:opacity-60'
  return 'btn-secondary h-10 px-4 text-xs'
}
function loadingLabel(action: string) {
  const lower = action.toLowerCase()
  if (lower.includes('approve')) return 'Approving...'
  if (lower.includes('reject')) return 'Rejecting...'
  return 'Processing...'
}
function executiveSummary(detail: WorkflowDocumentDetail) {
  const total = detail.summary?.grand_total || detail.summary?.grandTotal
  const currency = detail.summary?.currency
  const party = detail.summary?.supplier || detail.summary?.customer || detail.summary?.party || detail.summary?.party_name
  const state = detail.workflowState || detail.workflow_state || detail.status || 'pending review'
  return `${detail.doctype} ${detail.name} is ${state}. ${party ? `Party: ${party}. ` : ''}${total ? `Total: ${currency || ''} ${Number(total).toLocaleString()}. ` : ''}Review the document details and choose an available ERPNext workflow action when ready.`
}
