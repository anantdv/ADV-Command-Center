import { UploadCloud } from 'lucide-react'
import { useState } from 'react'
import { useDocumentUpload, useProcessDocument } from '../../hooks/api/useDocumentIntake'
import type { DocumentMappingPreview, DocumentUploadResponse } from '../../types/documentIntake'

export function DocumentUploadPanel({onProcessed}:{onProcessed?:(preview:DocumentMappingPreview)=>void}){
 const [uploaded,setUploaded]=useState<DocumentUploadResponse|null>(null);const upload=useDocumentUpload();const process=useProcessDocument()
 const onFile=(file?:File)=>{if(!file)return;upload.mutate(file,{onSuccess:setUploaded})}
 const processNow=()=>uploaded&&process.mutate(uploaded.intake_id,{onSuccess:onProcessed})
 return <section className="rounded-2xl border border-dashed border-indigo-200 bg-indigo-50/40 p-5"><label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl bg-white p-6 text-center shadow-sm"><UploadCloud className="text-indigo-500"/><span className="mt-2 text-sm font-semibold text-slate-900">Upload Supplier Invoice / Customer PO</span><span className="mt-1 text-xs text-slate-500">PDF, PNG, JPG, or text. OCR runs locally before draft creation.</span><input type="file" accept=".pdf,.png,.jpg,.jpeg,.txt" className="hidden" onChange={event=>onFile(event.target.files?.[0])}/></label>{uploaded&&<div className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-white p-3 text-xs"><span className="font-medium text-slate-700">{uploaded.file_name}</span><button onClick={processNow} disabled={process.isPending} className="btn-primary h-9 px-3 text-xs">{process.isPending?'Processing...':'Process OCR'}</button></div>}{(upload.error||process.error)&&<p className="mt-2 text-xs text-rose-600">{(upload.error||process.error)?.message}</p>}</section>
}
