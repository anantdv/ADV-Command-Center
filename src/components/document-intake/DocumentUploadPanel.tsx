import { UploadCloud } from 'lucide-react'
import { useState } from 'react'
import { useDocumentUpload, useProcessDocument } from '../../hooks/api/useDocumentIntake'
import type { DocumentMappingPreview, DocumentUploadResponse, IntakeSourceDocumentType } from '../../types/documentIntake'

const routes:{id:IntakeSourceDocumentType;title:string;subtitle:string;target:string}[]=[
 {id:'supplier_invoice',title:'Supplier Invoice',subtitle:'Create a draft Purchase Invoice',target:'Purchase Invoice'},
 {id:'customer_purchase_order',title:'Customer Purchase Order',subtitle:'Create a draft Sales Order',target:'Sales Order'},
]

export function DocumentUploadPanel({onProcessed}:{onProcessed?:(preview:DocumentMappingPreview)=>void}){
 const [sourceDocumentType,setSourceDocumentType]=useState<IntakeSourceDocumentType>('supplier_invoice')
 const [uploaded,setUploaded]=useState<DocumentUploadResponse|null>(null);const upload=useDocumentUpload();const process=useProcessDocument()
 const selected=routes.find(route=>route.id===sourceDocumentType) || routes[0]
 const onFile=(file?:File)=>{if(!file)return;upload.mutate({file,sourceDocumentType},{onSuccess:setUploaded})}
 const processNow=()=>uploaded&&process.mutate(uploaded.intake_id,{onSuccess:onProcessed})
 return <section className="rounded-2xl border border-dashed border-indigo-200 bg-indigo-50/40 p-5">
  <div className="mb-4">
   <p className="text-xs font-bold uppercase tracking-wide text-slate-400">Choose document route</p>
   <div className="mt-2 grid gap-2 sm:grid-cols-2">{routes.map(route=><button key={route.id} type="button" onClick={()=>{setSourceDocumentType(route.id);setUploaded(null)}} className={`rounded-2xl border p-3 text-left transition ${sourceDocumentType===route.id?'border-indigo-300 bg-white shadow-sm ring-2 ring-indigo-100':'border-slate-200 bg-white/70 hover:bg-white'}`}>
    <span className="block text-sm font-bold text-slate-900">{route.title}</span>
    <span className="mt-1 block text-xs text-slate-500">{route.subtitle}</span>
    <span className="mt-2 inline-flex rounded-full bg-slate-100 px-2 py-1 text-[10px] font-bold text-slate-500">Target: {route.target}</span>
   </button>)}</div>
  </div>
  <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl bg-white p-6 text-center shadow-sm"><UploadCloud className="text-indigo-500"/><span className="mt-2 text-sm font-semibold text-slate-900">Upload {selected.title}</span><span className="mt-1 text-xs text-slate-500">PDF, PNG, JPG, JPEG, WEBP, DOCX, or text. OCR runs before draft creation.</span><input type="file" accept=".pdf,.png,.jpg,.jpeg,.webp,.docx,.txt" className="hidden" onChange={event=>onFile(event.target.files?.[0])}/></label>
  {uploaded&&<div className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-white p-3 text-xs"><div><span className="block font-medium text-slate-700">{uploaded.file_name}</span><span className="text-slate-400">{selected.title} → {selected.target}</span></div><button onClick={processNow} disabled={process.isPending} className="btn-primary h-9 px-3 text-xs">{process.isPending?'Processing...':'Process OCR'}</button></div>}
  {(upload.error||process.error)&&<p className="mt-2 text-xs text-rose-600">{(upload.error||process.error)?.message}</p>}
 </section>
}
