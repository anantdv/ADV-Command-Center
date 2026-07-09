import { Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

export function ModuleHeader({ label, description, doctypes = [], onAskAi, onCreateDraft }: { label: string; description?: string; doctypes?: string[]; onAskAi?:()=>void; onCreateDraft?:()=>void }) {
  const moduleSlug=label.toLowerCase()
  return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <p className="eyebrow">ERP module workspace</p>
        <h1 className="mt-2 font-[Manrope] text-2xl font-bold text-slate-950">{label}</h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-500">{description || 'Permission-aware ERPNext workspace with scoped AI commands.'}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {onAskAi&&<button onClick={onAskAi} className="btn-primary"><Sparkles size={14}/>Ask AI about {label}</button>}
        {onCreateDraft&&<button onClick={onCreateDraft} className="btn-secondary">Create Draft</button>}
      </div>
    </div>
    {doctypes.length>0&&<div className="mt-4 flex flex-wrap gap-2">{doctypes.map(doctype=><Link key={doctype} to={`/modules/${moduleSlug}/doctype/${encodeURIComponent(doctype)}`} className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-500 transition hover:bg-indigo-50 hover:text-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-300">{doctype}</Link>)}</div>}
  </div>
}
