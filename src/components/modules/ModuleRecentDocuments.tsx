import { FileText } from 'lucide-react'
import type { ModuleRecentDocument } from '../../types/module'
import { formatCurrency } from '../../utils/formatters'

export function ModuleRecentDocuments({ documents, onOpen }: { documents: ModuleRecentDocument[]; onOpen: (doc: ModuleRecentDocument) => void }) {
  return <section className="card overflow-hidden">
    <div className="border-b px-5 py-4"><h3 className="text-sm font-bold text-slate-900">Recent documents</h3><p className="mt-1 text-xs text-slate-400">Latest permitted Selling records from ERPNext.</p></div>
    <div className="divide-y">
      {documents.length===0&&<p className="px-5 py-8 text-center text-xs text-slate-400">No recent documents available.</p>}
      {documents.map(doc=><button key={`${doc.doctype}-${doc.name}`} onClick={()=>onOpen(doc)} className="flex w-full items-center gap-3 px-5 py-3.5 text-left hover:bg-indigo-50/50">
        <span className="flex size-9 items-center justify-center rounded-xl bg-slate-100 text-slate-500"><FileText size={16}/></span>
        <span className="min-w-0 flex-1"><span className="block truncate text-xs font-bold text-slate-800">{doc.doctype} · {doc.title || doc.name}</span><span className="mt-1 block truncate text-[10px] text-slate-400">{doc.party || doc.status || 'ERPNext document'}{doc.date?` · ${doc.date}`:''}</span></span>
        {doc.amount!==null&&doc.amount!==undefined&&<span className="text-xs font-bold text-slate-700">{formatCurrency(doc.amount,doc.currency||'INR')}</span>}
      </button>)}
    </div>
  </section>
}
