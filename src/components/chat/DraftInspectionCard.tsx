import { Eye } from 'lucide-react'
import type { DraftInspectionPart } from '../../types/chat'

export function DraftInspectionCard({ part }: { part: DraftInspectionPart }) {
  return <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
    <div className="flex items-center justify-between border-b bg-slate-50 px-4 py-3">
      <div className="flex items-center gap-2">
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-emerald-50 text-emerald-600"><Eye size={15}/></span>
        <div>
          <p className="text-xs font-bold text-slate-800">{part.doctype} Draft</p>
          <p className="text-[10px] text-slate-400">Read-only draft inspection{part.draft_version ? ` · Version ${part.draft_version}` : ''}</p>
        </div>
      </div>
      <span className="rounded-full bg-emerald-50 px-2 py-1 text-[9px] font-bold uppercase text-emerald-700">No changes made</span>
    </div>
    <div className="space-y-4 p-4">
      {part.sections.map(section => <section key={section.title}>
        <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">{section.title}</p>
        <div className="space-y-2">
          {section.rows.map((row, index) => <InspectionRow key={`${section.title}-${index}`} row={row}/>)}
        </div>
      </section>)}
    </div>
  </div>
}

function InspectionRow({ row }: { row: Record<string, unknown> }) {
  const label = String(row.label || row.item_name || row.item_code || 'Field')
  if ('uom' in row || 'qty' in row || 'rate' in row || 'warehouse' in row) {
    return <div className="rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-2">
      <div className="text-xs font-bold text-slate-800">{label}</div>
      <div className="mt-1 flex flex-wrap gap-2 text-[11px] text-slate-500">
        {Boolean(row.item_code) && <Badge label="Item" value={row.item_code}/>}
        {Boolean(row.uom) && <Badge label="UOM" value={row.uom}/>}
        {row.qty !== undefined && <Badge label="Qty" value={row.qty}/>}
        {row.rate !== undefined && <Badge label="Rate" value={row.rate}/>}
        {Boolean(row.warehouse) && <Badge label="Warehouse" value={row.warehouse}/>}
      </div>
    </div>
  }
  return <div className="grid gap-1 rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-2 text-xs sm:grid-cols-[150px_1fr]">
    <span className="font-semibold text-slate-500">{label}</span>
    <span className="font-bold text-slate-800">{formatValue(row.value)}</span>
    {Boolean(row.source) && <span className="text-[10px] text-slate-400 sm:col-start-2">Source: {formatValue(row.source)}</span>}
  </div>
}

function Badge({ label, value }: { label: string; value: unknown }) {
  return <span className="rounded-full bg-white px-2 py-1 font-semibold text-slate-600 ring-1 ring-slate-200">{label}: <span className="text-slate-900">{formatValue(value)}</span></span>
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  return typeof value === 'object' ? JSON.stringify(value) : String(value)
}
