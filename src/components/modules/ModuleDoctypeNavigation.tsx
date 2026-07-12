import type { ModuleDoctypeInfo } from '../../types/module'
import { ModuleDoctypeCard } from './ModuleDoctypeCard'

export function ModuleDoctypeNavigation({ moduleName, doctypes }: { moduleName: string; doctypes: ModuleDoctypeInfo[] }) {
  return <section>
    <div className="mb-3 flex items-end justify-between gap-3"><div><h2 className="text-sm font-bold text-slate-900">Standard navigation</h2><p className="mt-1 text-xs text-slate-400">Open ERPNext list views.</p></div></div>
    {doctypes.length===0?<div className="card p-8 text-center text-xs text-slate-400">No DocTypes are available for your user.</div>:<div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{doctypes.map(item=><ModuleDoctypeCard key={item.doctype} moduleName={moduleName} item={item}/>)}</div>}
  </section>
}
