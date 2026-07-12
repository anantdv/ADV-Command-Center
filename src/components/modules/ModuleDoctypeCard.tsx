import { ArrowRight, Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { ModuleDoctypeInfo } from '../../types/module'
import { colorFromText } from '../../theme/colors'

export function ModuleDoctypeCard({ moduleName, item }: { moduleName: string; item: ModuleDoctypeInfo }) {
  const navigate = useNavigate()
  const accent = colorFromText(item.doctype)
  const open = () => navigate(`/modules/${moduleName.toLowerCase()}/doctype/${encodeURIComponent(item.doctype)}`)
  const create = () => navigate(`/command-center?module=${encodeURIComponent(moduleName)}&prompt=${encodeURIComponent(`create ${item.doctype.toLowerCase()} draft`)}&autoRun=false`)
  return <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md" style={{borderTopColor:accent,borderTopWidth:3}}>
    <div className="flex items-start justify-between gap-3">
      <div><h3 className="text-sm font-bold text-slate-900">{item.label}</h3><p className="mt-1 min-h-9 text-xs leading-5 text-slate-500">{item.description}</p></div>
      {item.recordCount!==null&&item.recordCount!==undefined&&<span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-bold text-slate-500">{item.recordCount}</span>}
    </div>
    <div className="mt-4 flex gap-2">
      <button onClick={open} className="btn-secondary flex-1">Open List<ArrowRight size={14}/></button>
      {item.canCreate&&<button onClick={create} className="flex size-9 items-center justify-center rounded-xl hover:opacity-85" style={{backgroundColor:`${accent}16`,color:accent}} title="Create draft in Command Center"><Plus size={15}/></button>}
    </div>
  </article>
}
