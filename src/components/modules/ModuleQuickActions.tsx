import { ArrowRight, Sparkles } from 'lucide-react'
import type { ModuleQuickAction } from '../../types/module'

export function ModuleQuickActions({ actions, onPrompt }: { actions: ModuleQuickAction[]; onPrompt: (prompt: string) => void }) {
  return <section className="card p-5">
    <div className="flex items-center gap-2"><Sparkles size={16} className="text-indigo-600"/><h3 className="text-sm font-bold text-slate-900">Quick actions</h3></div>
    <div className="mt-4 space-y-2">
      {actions.map(action=><button key={action.id} disabled={action.enabled===false} onClick={()=>onPrompt(action.prompt)} className="flex w-full items-center justify-between rounded-xl border border-slate-100 px-3 py-2.5 text-left text-xs font-semibold text-slate-600 transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700 disabled:cursor-not-allowed disabled:opacity-50">{action.label}<ArrowRight size={14}/></button>)}
      {actions.length===0&&<p className="text-xs text-slate-400">No quick actions are available with your current permissions.</p>}
    </div>
  </section>
}
