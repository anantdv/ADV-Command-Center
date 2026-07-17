import type { DocumentMappingPreview as Preview } from '../../types/documentIntake'
import { ExtractedLineItemsTable } from './ExtractedLineItemsTable'
import { OcrEditableHeaderFields } from './OcrEditableHeaderFields'
import { OcrPartySelector } from './OcrPartySelector'
import { OcrRawTextViewer } from './OcrRawTextViewer'
import { OcrExtractionDebugPanel } from './OcrExtractionDebugPanel'
import { documentIntakeService } from '../../services/documentIntakeService'
import { useEffect, useMemo, useRef, useState } from 'react'

export function DocumentMappingPreview({preview,onConfirm,onCancel,busy=false}:{preview:Preview;onConfirm?:()=>void;onCancel?:()=>void;busy?:boolean}){
 const [payload,setPayload]=useState<Record<string,unknown>>({...preview.draft_payload,items:(preview.draft_payload.items as unknown[])||preview.extracted_fields.items||[]})
 const [serverPreview,setServerPreview]=useState(preview)
 const [saving,setSaving]=useState(false)
 const [autoSaving,setAutoSaving]=useState(false)
 const [error,setError]=useState<string|null>(null)
 const dirty=useRef(false)
 const partyField=preview.target_doctype==='Purchase Invoice'?'supplier':'customer'
 const partyExtraction=serverPreview.field_extractions?.find(field=>field.fieldname===partyField)
 const items=(payload.items as NonNullable<Preview['extracted_fields']['items']>)||[]
 const validation=useMemo(()=>validate(payload,serverPreview.target_doctype,serverPreview.blocking_errors,serverPreview.invalid_reason),[payload,serverPreview.target_doctype,serverPreview.blocking_errors,serverPreview.invalid_reason])
 const setField=(key:string,value:unknown)=>{dirty.current=true;setPayload(current=>({...current,[key]:value}))}
 const save=async()=>{const updated=await documentIntakeService.updateMappingPreview(preview.intake_id,{target_doctype:preview.target_doctype,draft_payload:payload});setServerPreview(updated);return updated}
 useEffect(()=>{if(!dirty.current)return;const handle=window.setTimeout(()=>{setAutoSaving(true);setError(null);save().catch(err=>setError(err instanceof Error?err.message:'Could not save edited mapping.')).finally(()=>setAutoSaving(false))},800);return()=>window.clearTimeout(handle)},[payload])
  const saveAndConfirm=async()=>{if(validation)return;setSaving(true);setError(null);try{const updated=await save();if(updated.valid!==false)onConfirm?.();else setError(updated.invalid_reason||'Please complete required fields before creating the draft.')}catch(err){setError(err instanceof Error?err.message:'Could not save edited mapping.')}finally{setSaving(false)}}
 const useSupplierLine=(line:string)=>{dirty.current=true;setPayload(current=>({...current,[partyField]:line}))}
 const warnings=[...new Set(serverPreview.warnings||[])]
 return <section className="max-h-[82vh] overflow-y-auto rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
  <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs uppercase tracking-wide text-slate-400">{preview.source_document_type.replaceAll('_',' ')}</p><h3 className="text-lg font-bold text-slate-900">Create Draft {preview.target_doctype}</h3></div><span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">Review required</span></div>
  {warnings.length>0&&<div className="mt-4 rounded-xl bg-amber-50 p-3 text-xs text-amber-800"><p className="font-bold">Review required:</p><ul className="mt-1 list-disc space-y-1 pl-4">{warnings.map(warning=><li key={warning}>{warning}</li>)}</ul></div>}
  <div className="mt-4 rounded-2xl border border-slate-200 p-4">
   <div className="mb-3"><h4 className="text-sm font-bold text-slate-900">Scanned field data</h4><p className="text-xs text-slate-500">Values extracted from the uploaded document. Edit anything that looks wrong.</p></div>
   <OcrEditableHeaderFields payload={payload} fields={serverPreview.field_extractions} onChange={setField}/>
   <div className="mt-5"><h4 className="mb-2 text-sm font-bold text-slate-800">Scanned line items</h4><ExtractedLineItemsTable items={items} onChange={next=>setField('items',next)}/></div>
  </div>
  <div className="mt-4 rounded-2xl border border-indigo-100 bg-indigo-50/30 p-4">
   <div className="mb-3"><h4 className="text-sm font-bold text-slate-900">ERPNext nearest matching data</h4><p className="text-xs text-slate-500">Select the correct ERPNext party and item matches if auto-match is not accurate.</p></div>
   <OcrPartySelector field={partyExtraction} value={String(payload[partyField]||'')} onChange={value=>setField(partyField,value)}/>
  </div>
  {serverPreview.missing_fields.length>0&&<div className="mt-4 rounded-xl bg-rose-50 p-3 text-xs text-rose-700">Missing required fields: {serverPreview.missing_fields.map(field=>String(field.label||field.fieldname)).join(', ')}</div>}
  {validation&&<div className="mt-4 rounded-xl bg-rose-50 p-3 text-xs text-rose-700">{validation}</div>}
  {error&&<div className="mt-4 rounded-xl bg-rose-50 p-3 text-xs text-rose-700">{error}</div>}
  {serverPreview.extraction_debug_available&&<OcrExtractionDebugPanel intakeId={preview.intake_id} onUseSupplierSearch={useSupplierLine}/>}
  <OcrRawTextViewer text={serverPreview.raw_text_preview}/>
  <div className="sticky bottom-0 -mx-5 -mb-5 mt-5 flex items-center justify-end gap-2 border-t bg-white/95 p-4 backdrop-blur">{autoSaving&&<span className="mr-auto text-[10px] font-bold text-slate-400">Saving edits…</span>}{onCancel&&<button onClick={onCancel} className="btn-secondary h-10 px-4 text-sm">Cancel</button>}{onConfirm&&<button onClick={saveAndConfirm} disabled={busy||saving||Boolean(validation)} title={validation||'Create draft'} className="btn-primary h-10 px-4 text-sm disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500">{saving?'Saving…':'Confirm Create Draft'}</button>}</div>
 </section>
}

function validate(payload:Record<string,unknown>,target:string,blockingErrors?:string[],serverReason?:string|null){
 const party=target==='Purchase Invoice'?'supplier':'customer'
 if(!payload[party])return `Please select ${party === 'supplier' ? 'Supplier' : 'Customer'} before creating the draft.`
 if(target==='Purchase Invoice'&&!payload.posting_date)return 'Posting Date is required before creating the draft.'
 const items=(payload.items as Array<Record<string,unknown>>)||[]
 if(!items.length)return 'Please add at least one item before creating the draft.'
 if(items.some(item=>!item.item_code||Number(item.qty||0)<=0))return 'Every line item must have an Item Code and valid Qty before creating the draft.'
 return blockingErrors?.[0]||serverReason||null
}
