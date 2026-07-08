import { useState } from 'react'
import type { SuggestedPrompt } from '../../types/suggestions'
import { SuggestedActionButton } from './SuggestedActionButton'

export function SuggestedPromptButtons({suggestions=[],onSuggestionClick}:{suggestions?:SuggestedPrompt[];onSuggestionClick:(suggestion:SuggestedPrompt)=>void}){
  const [busy,setBusy]=useState<string|null>(null)
  const visible=suggestions.slice(0,6)
  if(!visible.length)return null
  const click=(suggestion:SuggestedPrompt)=>{
    if(suggestion.disabled)return
    setBusy(suggestion.id)
    try{onSuggestionClick(suggestion)}finally{window.setTimeout(()=>setBusy(null),450)}
  }
  return <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3">
    {visible.map(suggestion=><SuggestedActionButton key={suggestion.id} suggestion={suggestion} busy={busy===suggestion.id} onClick={click}/>)}
  </div>
}
