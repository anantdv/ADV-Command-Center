import { AlertCircle, CheckCircle2, Database, LoaderCircle, ShieldCheck } from 'lucide-react'
import type { ToolCallPart } from '../../types/chat'

export function ToolExecutionCard({ part }: { part: ToolCallPart }) {
  const name = part.tool_name || part.toolName || 'erp_tool'
  const title = name.split('_').map(word => word[0]?.toUpperCase() + word.slice(1)).join(' ')
  const StatusIcon = part.status === 'running' ? LoaderCircle : part.status === 'error' ? AlertCircle : CheckCircle2
  const tone = part.status === 'error' ? 'text-rose-500' : part.status === 'running' ? 'animate-spin text-indigo-500' : 'text-emerald-500'
  return <div className="my-3 rounded-xl border border-slate-200 bg-slate-50/70 p-3">
    <div className="flex items-center gap-3">
      <div className="flex size-8 items-center justify-center rounded-lg bg-white text-indigo-600 shadow-sm"><Database size={15}/></div>
      <div className="min-w-0 flex-1"><p className="text-xs font-bold text-slate-700">{title}</p><p className="mt-0.5 truncate text-[10px] text-slate-400">{part.input_summary || 'Permission-aware ERPNext query'}</p></div>
      <StatusIcon size={16} className={tone}/>
    </div>
    <div className="mt-2 flex items-center justify-between gap-3 text-[10px] font-semibold"><span className="inline-flex items-center gap-1 text-emerald-700"><ShieldCheck size={11}/>Permission checked</span>{part.output_summary&&<span className="truncate text-slate-400">{part.output_summary}</span>}</div>
  </div>
}
