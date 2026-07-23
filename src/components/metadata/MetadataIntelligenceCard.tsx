import { Database, GitBranch, Link2, Table2 } from 'lucide-react'
import type { ReactNode } from 'react'
import type { DoctypeIntelligence } from '../../types/metadata'

export function MetadataIntelligenceCard({ metadata }: { metadata: DoctypeIntelligence }) {
  return <div className="rounded-xl border border-slate-200 bg-white p-4">
    <div className="flex flex-wrap items-center gap-2">
      <span className="flex size-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600"><Database size={15}/></span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold text-slate-800">{metadata.doctype}</p>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">{metadata.module || 'ERPNext'} metadata intelligence</p>
      </div>
      {metadata.is_submittable&&<span className="rounded-full bg-amber-50 px-2 py-1 text-[9px] font-bold text-amber-700">Submittable</span>}
    </div>
    <div className="mt-4 grid gap-2 sm:grid-cols-4">
      <Metric icon={<Database size={14}/>} label="Fields" value={metadata.fields.length}/>
      <Metric icon={<Link2 size={14}/>} label="Links" value={metadata.link_fields.length}/>
      <Metric icon={<Table2 size={14}/>} label="Child Tables" value={metadata.child_tables.length}/>
      <Metric icon={<GitBranch size={14}/>} label="Required" value={metadata.mandatory_fields.length}/>
    </div>
    {metadata.child_tables.length>0&&<div className="mt-4">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Child tables</p>
      <div className="mt-2 flex flex-wrap gap-2">{metadata.child_tables.map(table=><span key={table.fieldname} className="rounded-full bg-slate-50 px-2.5 py-1 text-[10px] font-bold text-slate-600 ring-1 ring-slate-200">{table.label} → {table.child_doctype}</span>)}</div>
    </div>}
  </div>
}

function Metric({icon,label,value}:{icon:ReactNode;label:string;value:number}) {
  return <div className="rounded-lg bg-slate-50 p-3"><div className="flex items-center gap-2 text-slate-500">{icon}<span className="text-[10px] font-bold uppercase tracking-wider">{label}</span></div><p className="mt-1 text-lg font-extrabold text-slate-800">{value}</p></div>
}
