import type { FieldExtraction } from '../../types/documentIntake'
import { OcrConfidenceBadge } from './OcrConfidenceBadge'

export function OcrPartySelector({field,value,onChange}:{field?:FieldExtraction;value?:string;onChange:(value:string)=>void}){
  const candidates=field?.candidates||[]
  return <div className="rounded-xl border border-slate-200 p-3">
    <div className="mb-2 flex items-center justify-between"><label className="text-xs font-bold text-slate-700">{field?.label||'Party'}</label><OcrConfidenceBadge value={field?.confidence}/></div>
    <input value={value||''} onChange={event=>onChange(event.target.value)} placeholder={`Select ${field?.label||'party'}`} className="h-10 w-full rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-indigo-300"/>
    {field?.warning&&<p className="mt-2 text-[11px] text-amber-700">{field.warning}</p>}
    {candidates.length>0&&<div className="mt-3 space-y-1">
      <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Possible matches</p>
      {candidates.map((candidate,index)=><button key={index} type="button" onClick={()=>onChange(String(candidate.name||''))} className="flex w-full items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-left text-xs hover:bg-indigo-50">
        <span className="font-semibold text-slate-700">{String(candidate.supplier_name||candidate.customer_name||candidate.name||'')}</span>
        <span className="text-slate-400">{Math.round(Number(candidate.score||0)*100)}%</span>
      </button>)}
    </div>}
  </div>
}
