import { Loader2, Search, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { useSendChatMessage } from '../../hooks/api/useChat'
import type { ChildRowsResolutionPart, EntityMatch } from '../../types/chat'

export function ChildRowsResolutionCard({part}:{part:ChildRowsResolutionPart}){
  const send=useSendChatMessage()
  const [selected,setSelected]=useState<string>()
  const choose=(rowId:string,fieldname:string,value:string)=>{
    setSelected(`${rowId}:${value}`)
    send.mutate({
      conversation_id:part.draft_session_id,
      message:`Selected ${value}`,
      source:'generated_action',
      structured_action:{
        action:'select_entity_match',
        draft_session_id:part.draft_session_id,
        resolution_id:rowId,
        entity_scope:rowId.startsWith('parent-')?'header':'child_row',
        table_field:rowId.startsWith('parent-')?'__parent__':part.table_field,
        row_id:rowId,
        fieldname,
        selected_value:value,
        selected_doctype:fieldname==='item_code'?'Item':fieldname==='supplier'?'Supplier':fieldname==='customer'?'Customer':'',
      },
    })
  }
  return <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-4">
    <div className="flex items-start gap-3">
      <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-white text-amber-600 shadow-sm"><Search size={17}/></span>
      <div>
        <p className="text-sm font-extrabold text-slate-900">Select matching ERPNext records</p>
        <p className="mt-1 text-xs leading-5 text-slate-600">I extracted the rows below, but I need you to choose the real ERPNext record where the match is ambiguous. Quantities and rates are kept.</p>
      </div>
    </div>
    <div className="mt-4 space-y-3">
      {part.rows.map(row=><div key={row.row_id} className="rounded-xl border border-amber-100 bg-white p-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="text-xs font-bold text-slate-800">{row.source_text}</p>
            <p className="mt-1 text-[10px] font-semibold text-slate-400">{row.link_field.replaceAll('_',' ')} · query: {row.query}</p>
          </div>
          <Extracted data={row.extracted}/>
        </div>
        {row.matches.length?<div className="mt-3 grid gap-2">
          {row.matches.slice(0,5).map(match=><MatchButton key={match.value} match={match} busy={selected===`${row.row_id}:${match.value}`&&send.isPending} onClick={()=>choose(row.row_id,row.link_field,match.value)}/>)}
        </div>:<div className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700">No permitted active record matched this text. Try adding more detail or remove this row.</div>}
      </div>)}
    </div>
  </div>
}

function MatchButton({match,busy,onClick}:{match:EntityMatch;busy:boolean;onClick:()=>void}){
  return <button type="button" disabled={busy} onClick={onClick} className="flex w-full items-start gap-3 rounded-xl border border-slate-200 p-3 text-left transition hover:border-indigo-200 hover:bg-indigo-50 disabled:opacity-60">
    <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border border-slate-300 bg-white">{busy?<Loader2 size={12} className="animate-spin"/>:<ShieldCheck size={12} className="text-emerald-600"/>}</span>
    <span className="min-w-0 flex-1">
      <span className="block text-xs font-extrabold text-slate-800">{match.value} — {match.label}</span>
      <span className="mt-1 block text-[10px] leading-4 text-slate-500">{match.description || 'ERPNext record'}{match.metadata?.stock_uom?` | UOM: ${String(match.metadata.stock_uom)}`:''}{match.metadata?.item_group?` | ${String(match.metadata.item_group)}`:''}</span>
    </span>
    <span className="rounded-full bg-slate-100 px-2 py-1 text-[9px] font-bold text-slate-500">{Math.round(match.score*100)}%</span>
  </button>
}

function Extracted({data}:{data:Record<string,unknown>}){
  const entries=Object.entries(data).filter(([,value])=>value!==undefined&&value!==null&&value!=='')
  if(!entries.length)return null
  return <div className="flex flex-wrap gap-1">{entries.map(([key,value])=><span key={key} className="rounded-full bg-slate-100 px-2 py-1 text-[9px] font-bold text-slate-500">{key.replaceAll('_',' ')}: {String(value)}</span>)}</div>
}
