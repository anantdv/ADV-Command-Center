import { useState } from 'react'
import type { SuggestedPrompt } from '../../types/suggestions'
import { SuggestedActionButton } from './SuggestedActionButton'
import { capabilities, isExternalErpNextAction } from '../../config/capabilities'

export function SuggestedPromptButtons({suggestions=[],onSuggestionClick}:{suggestions?:SuggestedPrompt[];onSuggestionClick:(suggestion:SuggestedPrompt)=>void}){
  const [busy,setBusy]=useState<string|null>(null)
  const [expanded,setExpanded]=useState(false)
  const filtered=suggestions.filter(suggestion=>capabilities.erpnextExternalLinksEnabled||!isExternalErpNextAction(suggestion.actionType||suggestion.action_type||suggestion.type))
  const workflowFilters=filtered.filter(suggestion=>(suggestion.actionType||suggestion.action_type)==='filter_pending_approvals')
  const hasManyWorkflowFilters=workflowFilters.length>5
  const resetWorkflowIds=new Set(workflowFilters.filter(suggestion=>!suggestion.payload?.doctype).map(suggestion=>suggestion.id))
  const topWorkflowIds=new Set([...workflowFilters.filter(suggestion=>suggestion.payload?.doctype).slice(0,4).map(suggestion=>suggestion.id), ...resetWorkflowIds])
  const visible=hasManyWorkflowFilters&&!expanded
    ? filtered.filter(suggestion=>(suggestion.actionType||suggestion.action_type)!=='filter_pending_approvals'||topWorkflowIds.has(suggestion.id)).slice(0,7)
    : filtered.slice(0,10)
  if(!visible.length)return null
  const click=(suggestion:SuggestedPrompt)=>{
    if(suggestion.disabled)return
    setBusy(suggestion.id)
    try{onSuggestionClick(suggestion)}finally{window.setTimeout(()=>setBusy(null),450)}
  }
  return <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3">
    {visible.map(suggestion=><SuggestedActionButton key={suggestion.id} suggestion={suggestion} busy={busy===suggestion.id} onClick={click}/>)}
    {hasManyWorkflowFilters&&<button type="button" aria-expanded={expanded} onClick={()=>setExpanded(value=>!value)} className="inline-flex h-8 items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 text-[11px] font-bold text-slate-600 shadow-sm transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700">{expanded?'Less approval types':`More approval types · ${workflowFilters.length-4}`}</button>}
  </div>
}
