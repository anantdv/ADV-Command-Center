import type { FieldExtraction } from '../../types/documentIntake'
import { OcrConfidenceBadge } from './OcrConfidenceBadge'
import { useState } from 'react'
import { searchLink } from '../../services/erpnextService'

export function OcrPartySelector({field,value,onChange}:{field?:FieldExtraction;value?:string;onChange:(value:string)=>void}){
  const candidates=field?.candidates||[]
  const [query,setQuery]=useState('')
  const [results,setResults]=useState<Array<{name:string;label:string;description:string}>>([])
  const [searching,setSearching]=useState(false)
  const doctype=field?.fieldname==='customer'?'Customer':'Supplier'
  const runSearch=async()=>{setSearching(true);try{setResults(await searchLink(doctype,query||value||''))}finally{setSearching(false)}}
  return <div className="rounded-xl border border-slate-200 p-3">
    <div className="mb-2 flex items-center justify-between"><label className="text-xs font-bold text-slate-700">{field?.label||'Party'}</label><OcrConfidenceBadge value={field?.confidence}/></div>
    <input value={value||''} onChange={event=>onChange(event.target.value)} placeholder={`Select ${field?.label||'party'}`} className="h-10 w-full rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-indigo-300"/>
    {value&&<p className="mt-2 rounded-lg bg-emerald-50 px-3 py-2 text-[11px] font-semibold text-emerald-700">Selected: {value}</p>}
    {!value&&<p className="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-[11px] font-semibold text-rose-700">Supplier is required before creating the draft.</p>}
    {field?.warning&&<p className="mt-2 text-[11px] text-amber-700">{field.warning}</p>}
    {candidates.length>0&&<div className="mt-3 space-y-1">
      <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Possible matches</p>
      {candidates.map((candidate,index)=><button key={index} type="button" onClick={()=>onChange(String(candidate.name||''))} className="flex w-full items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-left text-xs hover:bg-indigo-50">
        <span className="font-semibold text-slate-700">{String(candidate.supplier_name||candidate.customer_name||candidate.name||'')}</span>
        <span className="text-slate-400">{Math.round(Number(candidate.score||0)*100)}%</span>
      </button>)}
    </div>}
    <div className="mt-3 flex gap-2"><input value={query} onChange={event=>setQuery(event.target.value)} placeholder={`Search ${doctype}`} className="h-9 min-w-0 flex-1 rounded-lg border border-slate-200 px-3 text-xs outline-none focus:border-indigo-300"/><button type="button" onClick={()=>void runSearch()} className="btn-secondary h-9 px-3 text-xs">{searching?'…':'Search'}</button></div>
    {results.length>0&&<div className="mt-2 space-y-1">{results.map(result=><button key={result.name} type="button" onClick={()=>onChange(result.name)} className="flex w-full items-center justify-between rounded-lg bg-white px-3 py-2 text-left text-xs ring-1 ring-slate-200 hover:bg-indigo-50"><span className="font-semibold">{result.label}</span><span className="text-slate-400">{result.name}</span></button>)}</div>}
  </div>
}
