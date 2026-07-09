import { Sparkles } from 'lucide-react'

export function ModuleHeader({ label, description, doctypes = [] }: { label: string; description?: string; doctypes?: string[] }) {
  return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <p className="eyebrow">ERP module workspace</p>
        <h1 className="mt-2 font-[Manrope] text-2xl font-bold text-slate-950">{label}</h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-500">{description || 'Permission-aware ERPNext workspace with scoped AI commands.'}</p>
      </div>
      <div className="rounded-2xl bg-indigo-50 px-4 py-3 text-xs font-bold text-indigo-700"><Sparkles size={14} className="mr-1 inline"/>Module AI enabled</div>
    </div>
    {doctypes.length>0&&<div className="mt-4 flex flex-wrap gap-2">{doctypes.map(doctype=><span key={doctype} className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-500">{doctype}</span>)}</div>}
  </div>
}
