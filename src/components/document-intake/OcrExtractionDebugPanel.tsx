import { useState } from 'react'
import type { ReactNode } from 'react'
import type { OcrExtractionDebug } from '../../types/documentIntake'
import { documentIntakeService } from '../../services/documentIntakeService'

export function OcrExtractionDebugPanel({intakeId,onUseSupplierSearch}:{intakeId:string;onUseSupplierSearch?:(line:string)=>void}){
  const [open,setOpen]=useState(false)
  const [loading,setLoading]=useState(false)
  const [debug,setDebug]=useState<OcrExtractionDebug|null>(null)
  const [error,setError]=useState<string|null>(null)
  const load=async()=>{
    if(debug){setOpen(value=>!value);return}
    setOpen(true);setLoading(true);setError(null)
    try{setDebug(await documentIntakeService.getExtractionDebug(intakeId))}
    catch(err){setError(err instanceof Error?err.message:'Could not load extraction debug.')}
    finally{setLoading(false)}
  }
  return <div className="mt-4 rounded-xl border border-dashed border-indigo-200 bg-indigo-50/30">
    <button type="button" onClick={()=>void load()} className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-bold text-indigo-700">
      <span>Show extraction debug</span><span>{open?'−':'+'}</span>
    </button>
    {open&&<div className="space-y-3 border-t border-indigo-100 p-3 text-xs">
      {loading&&<p className="text-slate-500">Loading extraction debug…</p>}
      {error&&<p className="rounded-lg bg-rose-50 p-2 text-rose-700">{error}</p>}
      {debug&&<>
        <div className="grid gap-2 sm:grid-cols-4">
          <Metric label="Source" value={debug.source||'unknown'}/>
          <Metric label="Text length" value={String(debug.text_length||0)}/>
          <Metric label="Tables" value={String(debug.tables_detected?.length||0)}/>
          <Metric label="Line candidates" value={String(debug.line_item_candidates?.length||0)}/>
        </div>
        {debug.supplier_candidates?.length>0&&<Panel title="Supplier candidates">
          {debug.supplier_candidates.map((candidate,index)=><div key={index} className="flex items-center justify-between rounded-lg bg-white px-3 py-2 ring-1 ring-indigo-100">
            <span className="font-semibold text-slate-700">{String(candidate.candidate_name||candidate.name||'')}</span>
            <span className="text-slate-400">{Math.round(Number(candidate.confidence||candidate.score||0)*100)}%</span>
          </div>)}
        </Panel>}
        <Panel title="Field candidates">
          {Object.entries(debug.field_candidates||{}).map(([field,candidates])=><div key={field} className="rounded-lg bg-white p-2 ring-1 ring-indigo-100">
            <p className="mb-1 font-bold text-slate-700">{field.replaceAll('_',' ')}</p>
            {candidates.length?candidates.slice(0,5).map((candidate,index)=><p key={index} className="text-slate-500">{String(candidate.value||'')} <span className="text-slate-300">· {String(candidate.reason||'candidate')}</span></p>):<p className="text-slate-300">No candidates</p>}
          </div>)}
        </Panel>
        <Panel title="First extracted lines">
          <div className="max-h-72 overflow-auto rounded-lg bg-slate-950 p-3 font-mono text-[11px] leading-5 text-slate-100">
            {(debug.first_lines||[]).map((line,index)=><div key={index} className="group flex gap-2 border-b border-white/5 py-1 last:border-0">
              <span className="w-7 shrink-0 text-slate-500">{index+1}</span>
              <button type="button" onClick={()=>onUseSupplierSearch?.(line)} className="hidden rounded bg-white/10 px-2 text-[10px] text-white group-hover:inline">Use as supplier search</button>
              <span>{line}</span>
            </div>)}
          </div>
        </Panel>
        {debug.warnings?.length>0&&<Panel title="Warnings">{debug.warnings.map(warning=><p key={warning} className="rounded bg-amber-50 p-2 text-amber-800">{warning}</p>)}</Panel>}
      </>}
    </div>}
  </div>
}

function Metric({label,value}:{label:string;value:string}){
  return <div className="rounded-lg bg-white p-2 ring-1 ring-indigo-100"><p className="text-[10px] uppercase tracking-wide text-slate-400">{label}</p><p className="font-bold text-slate-800">{value}</p></div>
}

function Panel({title,children}:{title:string;children:ReactNode}){
  return <div><p className="mb-2 text-[10px] font-bold uppercase tracking-wide text-slate-400">{title}</p><div className="space-y-2">{children}</div></div>
}
