import type { FieldExtraction } from '../../types/documentIntake'
import { OcrConfidenceBadge } from './OcrConfidenceBadge'

type Props={payload:Record<string,unknown>;fields?:FieldExtraction[];onChange:(key:string,value:unknown)=>void}

export function OcrEditableHeaderFields({payload,fields=[],onChange}:Props){
  const keys=['bill_no','bill_date','posting_date','due_date','currency','grand_total','tax_amount']
  return <div className="grid gap-3 sm:grid-cols-2">
    {keys.map(key=>{const extraction=fields.find(field=>field.fieldname===key);return <div key={key} className="rounded-xl bg-slate-50 p-3">
      <div className="mb-1 flex items-center justify-between"><label className="text-[10px] font-bold uppercase text-slate-400">{key.replaceAll('_',' ')}</label>{extraction&&<OcrConfidenceBadge value={extraction.confidence}/>}</div>
      <input value={String(payload[key]??'')} onChange={event=>onChange(key,event.target.value)} className="h-9 w-full rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-indigo-300"/>
      {(extraction?.candidates?.length||0)>0&&<div className="mt-2 flex flex-wrap gap-1">{extraction?.candidates.slice(0,3).map((candidate,index)=><button key={index} type="button" onClick={()=>onChange(key,candidate.value)} className="rounded-full bg-white px-2 py-1 text-[10px] font-semibold text-indigo-700 ring-1 ring-indigo-100 hover:bg-indigo-50">{String(candidate.value||'')}</button>)}</div>}
      {extraction?.warning&&<p className="mt-1 text-[10px] text-amber-700">{extraction.warning}</p>}
    </div>})}
  </div>
}
