import { useState } from 'react'
import { CheckCircle2, FileText } from 'lucide-react'
import { formatCurrency } from '../../utils/formatters'
import { useAuthStore } from '../../store/useAuthStore'
import type { RecordDetailPart } from '../../types/chat'
import { BusinessGraphPanel } from '../graph/BusinessGraphPanel'
import { WorkflowActionButtons } from '../workflow/WorkflowActionButtons'
import type { ApplyWorkflowActionResponse, WorkflowAction } from '../../types/workflow'

export function RecordDetailCard({ data }: { data: RecordDetailPart }) {
  const [appliedWorkflow, setAppliedWorkflow] = useState<ApplyWorkflowActionResponse | null>(null)
  const currency = useAuthStore(state => state.user?.companyCurrency) || String(data.summary?.currency || 'INR')
  const items = data.items || []
  const summaryEntries = Object.entries(data.summary || {}).filter(([, value]) => value !== null && value !== undefined && value !== '')
  const fieldEntries = Object.entries(data.fields || {})
    .filter(([key, value]) => !key.startsWith('_') && !summaryEntries.some(([summaryKey]) => summaryKey === key) && value !== null && value !== undefined && value !== '')
    .slice(0, 12)
  const workflowState = appliedWorkflow?.newState || appliedWorkflow?.new_state || data.workflow_state
  const actionsSource = appliedWorkflow ? (appliedWorkflow.availableActions || appliedWorkflow.available_actions || []) : (data.available_workflow_actions || [])
  const actions = actionsSource.map(action => typeof action === 'string' ? { action } : action as WorkflowAction)
  return <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
    <div className="flex flex-wrap items-start justify-between gap-3 border-b bg-slate-50/70 px-4 py-3">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex size-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600"><FileText size={17}/></span>
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-slate-400">{data.doctype}</p>
          <h3 className="text-sm font-bold text-slate-900">{data.title || data.name}</h3>
          <p className="mt-0.5 text-xs text-slate-500">{data.name}</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {data.status&&<span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-bold text-slate-600">{data.status}</span>}
        {workflowState&&<span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-700">{workflowState}</span>}
        {data.docstatus!==null&&data.docstatus!==undefined&&<span className="rounded-full bg-indigo-50 px-2 py-1 text-[10px] font-bold text-indigo-600">Docstatus {data.docstatus}</span>}
      </div>
    </div>
    {summaryEntries.length>0&&<div className="grid gap-2 border-b p-4 sm:grid-cols-2 lg:grid-cols-3">
      {summaryEntries.map(([key,value])=><InfoTile key={key} label={label(key)} value={formatValue(key,value,currency)}/>)}
    </div>}
    {fieldEntries.length>0&&<div className="grid gap-x-5 gap-y-3 border-b p-4 sm:grid-cols-2">
      {fieldEntries.map(([key,value])=><div key={key} className="min-w-0"><p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{label(key)}</p><p className="truncate text-xs font-semibold text-slate-700">{formatValue(key,value,currency)}</p></div>)}
    </div>}
    {items.length>0&&<div className="border-b p-4">
      <p className="mb-2 text-xs font-bold text-slate-800">Items</p>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-xs">
          <thead><tr className="border-b text-[10px] uppercase tracking-wide text-slate-400">{Object.keys(items[0]).filter(key=>!key.startsWith('_')).slice(0,8).map(key=><th key={key} className="px-3 py-2">{label(key)}</th>)}</tr></thead>
          <tbody>{items.slice(0,10).map((item,index)=><tr key={String(item.name || item.item_code || index)} className="border-b last:border-0">{Object.keys(items[0]).filter(key=>!key.startsWith('_')).slice(0,8).map(key=><td key={key} className="px-3 py-2 text-slate-600">{formatValue(key,item[key],currency)}</td>)}</tr>)}</tbody>
        </table>
      </div>
    </div>}
    <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
      <div className="flex flex-wrap gap-2">
        {actions.length>0?<WorkflowActionButtons doctype={data.doctype} name={data.name} actions={actions} onApplied={setAppliedWorkflow}/>:<span className="text-[10px] font-semibold text-slate-400">No workflow actions available</span>}
      </div>
    </div>
    {appliedWorkflow && <div className="mx-4 mb-4 flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs font-semibold text-emerald-700">
      <CheckCircle2 size={15} className="mt-0.5 shrink-0"/>
      <span>ERPNext workflow action “{appliedWorkflow.action}” was applied successfully. New state: {workflowState || 'updated'}.</span>
    </div>}
    <BusinessGraphPanel doctype={data.doctype} name={data.name}/>
  </div>
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
    <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{label}</p>
    <p className="mt-1 truncate text-xs font-bold text-slate-800">{value}</p>
  </div>
}

function label(key: string) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase())
}

function formatValue(key: string, value: unknown, currency: string) {
  if(value === null || value === undefined || value === '') return '—'
  if(typeof value === 'number' && /(amount|total|rate|price|outstanding|balance)/i.test(key)) return formatCurrency(value, currency)
  if(typeof value === 'number') return new Intl.NumberFormat('en-IN').format(value)
  if(typeof value === 'boolean') return value ? 'Yes' : 'No'
  if(typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
