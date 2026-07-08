import { Download, ExternalLink, FileSpreadsheet, GitBranch, LayoutDashboard, Loader2, Navigation, PenLine, Pin, RefreshCw, Sparkles, TriangleAlert } from 'lucide-react'
import type { SuggestedPrompt } from '../../types/suggestions'

const icons:Record<string,typeof Sparkles>={
  prompt:Sparkles,
  export:FileSpreadsheet,
  pin:Pin,
  navigation:Navigation,
  workflow_action:GitBranch,
  crud_confirmation:PenLine,
  download_file:Download,
  open_library:ExternalLink,
  retry:RefreshCw,
}

export function SuggestedActionButton({suggestion,busy,onClick}:{suggestion:SuggestedPrompt;busy?:boolean;onClick:(suggestion:SuggestedPrompt)=>void}){
  const actionType=suggestion.actionType||suggestion.action_type||suggestion.type
  const Icon=busy?Loader2:(icons[actionType]||icons[suggestion.type]||Sparkles)
  const disabled=Boolean(suggestion.disabled||busy)
  const reason=suggestion.disabledReason||suggestion.disabled_reason||suggestion.label
  const risk=suggestion.risk||'low'
  const style=risk==='high'?'border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100':risk==='medium'?'border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100':'border-slate-200 bg-white text-slate-600 hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700'
  return <button type="button" disabled={disabled} title={reason||suggestion.label} onClick={()=>onClick(suggestion)} className={`inline-flex h-8 items-center gap-1.5 rounded-full border px-3 text-[11px] font-bold shadow-sm transition disabled:cursor-not-allowed disabled:opacity-45 ${style}`}>
    <Icon size={13} className={busy?'animate-spin':''}/>
    {risk==='high'&&<TriangleAlert size={12}/>}
    <span>{suggestion.label}</span>
  </button>
}
