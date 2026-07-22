import { useMemo, useState } from 'react'
import { Loader2, Send } from 'lucide-react'
import { useContinueCrud } from '../../hooks/api/useChat'
import type { MissingFieldsPart } from '../../types/chat'

export function MissingFieldsForm({part}:{part:MissingFieldsPart}){
  const initial=useMemo(()=>Object.fromEntries(part.fields.map(field=>[field.fieldname,''])),[part.fields])
  const [values,setValues]=useState<Record<string,string>>(initial)
  const [localError,setLocalError]=useState<string>()
  const continuation=useContinueCrud()
  const complete=part.fields.every(field=>values[field.fieldname]?.trim())
  const submit=()=>{
    const parsed=Object.fromEntries(part.fields.map(field=>[field.fieldname,values[field.fieldname]]))
    setLocalError(undefined)
    continuation.mutate({operation:part.operation,doctype:part.doctype,record_name:part.record_name,data:{...part.collected_data,...parsed},conversation_id:part.conversation_id,message_id:part.message_id})
  }
  return <div className="rounded-xl border border-indigo-200 bg-indigo-50/60 p-4"><p className="text-sm font-bold text-slate-800">Complete the {part.doctype} details</p><p className="mt-1 text-xs text-slate-500">Required fields are validated before a preview is created.</p><div className="mt-4 grid gap-3 sm:grid-cols-2">{part.fields.map(field=><label key={field.fieldname} className="text-[11px] font-bold text-slate-600"><span>{field.label}<span className="text-rose-500"> *</span></span>{field.options?<select value={values[field.fieldname]||''} onChange={event=>setValues(current=>({...current,[field.fieldname]:event.target.value}))} className="mt-1.5 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs outline-none focus:border-indigo-400"><option value="">Select {field.label}</option>{field.options.split('\n').map(option=><option key={option}>{option}</option>)}</select>:field.fieldtype==='Table'?<div className="mt-1.5 rounded-xl border border-slate-200 bg-white p-3"><textarea value={values[field.fieldname]||''} onChange={event=>setValues(current=>({...current,[field.fieldname]:event.target.value}))} placeholder={'Type item rows naturally, for example:\\nTV qty 1\\n20 bags sugar at 12 each\\nItem 12345 quantity 10 warehouse Main'} className="min-h-28 w-full resize-y text-xs outline-none"/><p className="mt-2 text-[10px] font-semibold text-slate-400">No JSON needed. Tinni will search ERPNext and ask you to select ambiguous matches.</p></div>:<input value={values[field.fieldname]||''} onChange={event=>setValues(current=>({...current,[field.fieldname]:event.target.value}))} className="mt-1.5 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs outline-none focus:border-indigo-400"/>}</label>)}</div><button type="button" disabled={!complete||continuation.isPending||continuation.isSuccess} onClick={submit} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-bold text-white hover:bg-indigo-700 disabled:opacity-50">{continuation.isPending?<Loader2 size={13} className="animate-spin"/>:<Send size={13}/>}Continue to review</button>{localError&&<p className="mt-2 text-xs font-semibold text-rose-700">{localError}</p>}{continuation.isSuccess&&<p className="mt-2 text-xs font-semibold text-emerald-700">Details saved. The confirmation preview has been added below.</p>}{continuation.isError&&<p className="mt-2 text-xs font-semibold text-rose-700">{continuation.error instanceof Error?continuation.error.message:'Unable to continue.'}</p>}</div>
}
