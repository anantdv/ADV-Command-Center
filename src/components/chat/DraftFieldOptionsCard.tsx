import { Loader2, MapPin, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { useSendChatMessage } from '../../hooks/api/useChat'
import type { DraftFieldOptionsPart } from '../../types/chat'

export function DraftFieldOptionsCard({part}:{part:DraftFieldOptionsPart}){
  const send=useSendChatMessage()
  const [selected,setSelected]=useState<string>()
  const choose=(value:string)=>{
    setSelected(value)
    send.mutate({
      conversation_id:part.draft_session_id,
      message:`Use ${value} for ${part.label}`,
      source:'generated_action',
      structured_action:{
        action:'select_draft_field_value',
        draft_session_id:part.draft_session_id,
        scope:part.row_ids.length?'selected_child_rows':'draft',
        table_field:part.table_field,
        row_ids:part.row_ids,
        fieldname:part.fieldname,
        selected_value:value,
      },
    })
  }
  return <div className="rounded-2xl border border-teal-200 bg-teal-50/70 p-4">
    <div className="flex items-start gap-3">
      <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-white text-teal-600 shadow-sm"><MapPin size={17}/></span>
      <div>
        <p className="text-sm font-extrabold text-slate-900">{part.label} required</p>
        <p className="mt-1 text-xs leading-5 text-slate-600">{part.message}</p>
      </div>
    </div>
    <div className="mt-4 grid gap-2">
      {part.options.length?part.options.map(option=><button key={option.value} type="button" disabled={Boolean(option.disabled)||selected===option.value&&send.isPending} onClick={()=>choose(option.value)} className="flex w-full items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 text-left transition hover:border-teal-300 hover:bg-white disabled:cursor-not-allowed disabled:opacity-60">
        <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border border-slate-300 bg-white">{selected===option.value&&send.isPending?<Loader2 size={12} className="animate-spin"/>:<ShieldCheck size={12} className={option.disabled?'text-slate-300':'text-emerald-600'}/>}</span>
        <span className="min-w-0 flex-1">
          <span className="block text-xs font-extrabold text-slate-800">{option.label}</span>
          <span className="mt-1 block text-[10px] leading-4 text-slate-500">{option.description||'ERPNext option'}{option.metadata?.company?` | ${String(option.metadata.company)}`:''}{option.reason?` | ${option.reason}`:''}</span>
        </span>
      </button>):<div className="rounded-lg bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700">No valid options were available for this field.</div>}
    </div>
  </div>
}
