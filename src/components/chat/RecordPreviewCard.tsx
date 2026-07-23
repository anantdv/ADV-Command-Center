import { ArrowRight, FilePenLine, PlusCircle } from 'lucide-react'
import type { RecordPreviewPart } from '../../types/chat'

const preferredOrder = [
  'supplier',
  'customer',
  'company',
  'transaction_date',
  'schedule_date',
  'posting_date',
  'due_date',
  'currency',
  'conversion_rate',
  'set_warehouse',
  'items',
  'net_total',
  'total_taxes_and_charges',
  'grand_total',
]

export function RecordPreviewCard({ part }: { part: RecordPreviewPart }) {
  const fields = orderedFields(part.after_data, part.totals)
  return <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
    <div className="flex items-center justify-between border-b bg-slate-50 px-4 py-3">
      <div className="flex items-center gap-2">
        {part.operation === 'create' ? <PlusCircle size={16} className="text-indigo-600"/> : <FilePenLine size={16} className="text-indigo-600"/>}
        <div>
          <p className="text-xs font-bold text-slate-800">{part.operation === 'create' ? `New ${part.doctype}` : `${part.doctype}: ${part.record_name}`}</p>
          <p className="text-[10px] text-slate-400">This will create a draft only. It will not submit or post the document.</p>
        </div>
      </div>
      <span className="rounded-full bg-amber-50 px-2 py-1 text-[9px] font-bold uppercase text-amber-700">Confirmation required</span>
    </div>
    {part.changes && part.changes.length > 0 && <div className="border-b bg-emerald-50 px-4 py-2 text-[10px] font-semibold text-emerald-700">
      Updated {part.changes.length} draft value{part.changes.length === 1 ? '' : 's'}. Please review the refreshed preview.
    </div>}
    <div className="divide-y divide-slate-100">
      {fields.map(field => <div key={field} className="grid gap-1 px-4 py-3 text-xs sm:grid-cols-[150px_1fr]">
        <span className="font-semibold text-slate-500">{label(field)}</span>
        {part.operation === 'update'
          ? <div className="flex flex-wrap items-center gap-2"><Value value={part.before_data?.[field]}/><ArrowRight size={13} className="text-slate-300"/><Value field={field} value={valueFor(field, part)} after/></div>
          : <Value field={field} value={valueFor(field, part)} after/>}
      </div>)}
    </div>
    <div className="border-t bg-indigo-50/50 px-4 py-2.5 text-[10px] font-semibold text-indigo-700">Confirmation required before ERPNext is changed.</div>
  </div>
}

function orderedFields(data: Record<string, unknown>, totals?: Record<string, unknown>) {
  const keys = new Set([...Object.keys(data || {}), ...Object.keys(totals || {})])
  const hidden = new Set(['field_sources'])
  const ordered = preferredOrder.filter(field => keys.has(field) && !hidden.has(field))
  const rest = [...keys].filter(field => !preferredOrder.includes(field) && !hidden.has(field))
  return [...ordered, ...rest]
}

function valueFor(field: string, part: RecordPreviewPart) {
  return part.after_data[field] ?? part.totals?.[field]
}

function label(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, character => character.toUpperCase())
}

function Value({ value, field, after = false }: { value: unknown; field?: string; after?: boolean }) {
  if (Array.isArray(value) && field === 'items') return <ItemsTable rows={value}/>
  return <span className={after ? 'font-semibold text-slate-800' : 'text-slate-400 line-through'}>{formatValue(value)}</span>
}

function ItemsTable({ rows }: { rows: unknown[] }) {
  return <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
    <table className="min-w-[720px] w-full text-left">
      <thead><tr className="border-b bg-slate-50">{['Item', 'Description', 'Qty', 'UOM', 'Warehouse', 'Rate', 'Amount'].map(column => <th key={column} className="px-3 py-2 text-[10px] font-bold uppercase text-slate-400">{column}</th>)}</tr></thead>
      <tbody>{rows.map((raw, index) => {
        const row = raw as Record<string, unknown>
        return <tr key={String(row.item_code || row.row_id || index)} className="border-b last:border-0">
          <td className="px-3 py-2 text-xs font-bold text-indigo-600">{formatValue(row.item_code || 'Unresolved')}</td>
          <td className="px-3 py-2 text-xs text-slate-600">{formatValue(row.item_name || row.description)}</td>
          <td className="px-3 py-2 text-xs text-slate-600">{formatValue(row.qty)}</td>
          <td className="px-3 py-2 text-xs text-slate-600">{formatValue(row.uom || row.stock_uom)}</td>
          <td className="px-3 py-2 text-xs text-slate-600">{formatValue(row.warehouse)}</td>
          <td className="px-3 py-2 text-xs text-slate-600">{formatValue(row.rate)}</td>
          <td className="px-3 py-2 text-xs font-semibold text-slate-800">{formatValue(row.amount)}</td>
        </tr>
      })}</tbody>
    </table>
  </div>
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
