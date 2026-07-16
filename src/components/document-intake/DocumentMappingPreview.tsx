import type { DocumentMappingPreview as Preview } from '../../types/documentIntake'
import { ExtractedLineItemsTable } from './ExtractedLineItemsTable'
import { OcrEditableHeaderFields } from './OcrEditableHeaderFields'
import { OcrPartySelector } from './OcrPartySelector'
import { OcrRawTextViewer } from './OcrRawTextViewer'
import { documentIntakeService } from '../../services/documentIntakeService'
import { useMemo, useState } from 'react'

export function DocumentMappingPreview({preview,onConfirm,onCancel,busy=false}:{preview:Preview;onConfirm?:()=>void;onCancel?:()=>void;busy?:boolean}){
 const [payload,setPayload]=useState<Record<string,unknown>>({...preview.draft_payload,items:(preview.draft_payload.items as unknown[])||preview.extracted_fields.items||[]})
 const [saving,setSaving]=useState(false)
 const [error,setError]=useState<string|null>(null)
 const partyField=preview.target_doctype==='Purchase Invoice'?'supplier':'customer'
 const partyExtraction=preview.field_extractions?.find(field=>field.fieldname===partyField)
 const items=(payload.items as NonNullable<Preview['extracted_fields']['items']>)||[]
 const validation=useMemo(()=>validate(payload,preview.target_doctype,preview.invalid_reason),[payload,preview.target_doctype,preview.invalid_reason])
 const setField=(key:string,value:unknown)=>setPayload(current=>({...current,[key]:value}))
 const saveAndConfirm=async()=>{if(validation)return;setSaving(true);setError(null);try{await documentIntakeService.updateMappingPreview(preview.intake_id,{target_doctype:preview.target_doctype,draft_payload:payload});onConfirm?.()}catch(err){setError(err instanceof Error?err.message:'Could not save edited mapping.')}finally{setSaving(false)}}
 return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
  <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs uppercase tracking-wide text-slate-400">{preview.source_document_type.replaceAll('_',' ')}</p><h3 className="text-lg font-bold text-slate-900">Create Draft {preview.target_doctype}</h3></div><span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">Review required</span></div>
  {preview.warnings.length>0&&<div className="mt-4 rounded-xl bg-amber-50 p-3 text-xs text-amber-800">{preview.warnings.join(' ')}</div>}
  <div className="mt-4"><OcrPartySelector field={partyExtraction} value={String(payload[partyField]||'')} onChange={value=>setField(partyField,value)}/></div>
  <div className="mt-4"><OcrEditableHeaderFields payload={payload} fields={preview.field_extractions} onChange={setField}/></div>
  <div className="mt-5"><h4 className="mb-2 text-sm font-bold text-slate-800">Line items</h4><ExtractedLineItemsTable items={items} onChange={next=>setField('items',next)}/></div>
  {preview.missing_fields.length>0&&<div className="mt-4 rounded-xl bg-rose-50 p-3 text-xs text-rose-700">Missing required fields: {preview.missing_fields.map(field=>String(field.label||field.fieldname)).join(', ')}</div>}
  {validation&&<div className="mt-4 rounded-xl bg-rose-50 p-3 text-xs text-rose-700">{validation}</div>}
  {error&&<div className="mt-4 rounded-xl bg-rose-50 p-3 text-xs text-rose-700">{error}</div>}
  <OcrRawTextViewer text={preview.raw_text_preview}/>
  <div className="mt-5 flex justify-end gap-2">{onCancel&&<button onClick={onCancel} className="btn-secondary h-10 px-4 text-sm">Cancel</button>}{onConfirm&&<button onClick={saveAndConfirm} disabled={busy||saving||Boolean(validation)} className="btn-primary h-10 px-4 text-sm">{saving?'Saving…':'Confirm Create Draft'}</button>}</div>
 </section>
}

function validate(payload:Record<string,unknown>,target:string,serverReason?:string|null){
 const party=target==='Purchase Invoice'?'supplier':'customer'
 if(!payload[party])return `Please select ${party === 'supplier' ? 'Supplier' : 'Customer'} before creating the draft.`
 if(target==='Purchase Invoice'&&!payload.posting_date)return 'Posting Date is required before creating the draft.'
 const items=(payload.items as Array<Record<string,unknown>>)||[]
 if(!items.length)return 'Please add at least one item before creating the draft.'
 if(items.some(item=>!item.item_code||Number(item.qty||0)<=0))return 'Every line item must have an Item Code and valid Qty before creating the draft.'
 return serverReason||null
}
