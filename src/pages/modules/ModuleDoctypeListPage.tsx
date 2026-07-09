import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Search } from 'lucide-react'
import { ErrorState } from '../../components/common/ErrorState'
import { LoadingState } from '../../components/common/LoadingState'
import { RecordDetailCard } from '../../components/results/RecordDetailCard'
import { useModuleDoctypeRecords } from '../../hooks/api/useModules'
import { getDocumentDetail } from '../../services/erpnextService'
import type { DocumentDetailResponse } from '../../types/erpnext'
import type { RecordDetailPart } from '../../types/chat'

export function ModuleDoctypeListPage(){
  const {moduleName='Selling',doctype='Customer'}=useParams()
  const navigate=useNavigate()
  const [page,setPage]=useState(1)
  const [search,setSearch]=useState('')
  const [detail,setDetail]=useState<DocumentDetailResponse|null>(null)
  const records=useModuleDoctypeRecords(moduleName,doctype,page,search)
  const openRow=async(row:Record<string,unknown>)=>{
    const meta=row._meta as {doctype?:string;name?:string}|undefined
    if(!meta?.doctype||!meta.name)return
    setDetail(await getDocumentDetail(meta.doctype,meta.name))
  }
  if(records.isLoading)return <LoadingState cards={5}/>
  if(records.isError||!records.data)return <ErrorState retry={()=>void records.refetch()} message="I could not load records for this document type."/>
  const totalPages=Math.max(1,Math.ceil(records.data.total/records.data.pageSize))
  return <div className="-m-4 min-h-[calc(100vh-72px)] bg-[#f8f9fc] p-4 sm:-m-6 sm:p-6 lg:-m-8 lg:p-8">
    <header className="mb-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="eyebrow">{moduleName} list view</p>
      <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div><h1 className="font-[Manrope] text-2xl font-bold text-slate-950">{doctype}</h1><p className="mt-1 text-sm text-slate-500">Permission-aware ERPNext records.</p></div>
        <div className="flex flex-wrap gap-2"><button className="btn-secondary" onClick={()=>navigate(`/command-center?module=${encodeURIComponent(moduleName)}&prompt=${encodeURIComponent(`show ${doctype}`)}&autoRun=true`)}>Open in Command Center</button><button className="btn-primary" onClick={()=>navigate(`/command-center?module=${encodeURIComponent(moduleName)}&prompt=${encodeURIComponent(`create ${doctype.toLowerCase()} draft`)}&autoRun=false`)}>Create Draft</button></div>
      </div>
      <div className="relative mt-4 max-w-md"><Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/><input value={search} onChange={event=>{setSearch(event.target.value);setPage(1)}} placeholder={`Search ${doctype}...`} className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm outline-none focus:border-indigo-300"/></div>
    </header>
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-xs">
          <thead><tr className="border-b bg-slate-50">{records.data.columns.map(column=><th key={column.key} className="px-4 py-3 text-[10px] uppercase tracking-wide text-slate-400">{column.label}</th>)}</tr></thead>
          <tbody>{records.data.rows.map((row,index)=><tr key={String(row.name||index)} onClick={()=>openRow(row)} className="cursor-pointer border-b last:border-0 hover:bg-indigo-50/60">{records.data!.columns.map(column=><td key={column.key} className="whitespace-nowrap px-4 py-3 text-slate-600">{formatValue(row[column.key])}</td>)}</tr>)}</tbody>
        </table>
      </div>
      {records.data.rows.length===0&&<div className="p-10 text-center text-xs text-slate-400">No records found.</div>}
      <footer className="flex items-center justify-between border-t px-4 py-3 text-xs text-slate-500"><span>Page {page} of {totalPages} · {records.data.total} records</span><span className="flex gap-2"><button className="btn-secondary h-8 px-3" disabled={page<=1} onClick={()=>setPage(value=>Math.max(1,value-1))}>Previous</button><button className="btn-secondary h-8 px-3" disabled={page>=totalPages} onClick={()=>setPage(value=>value+1)}>Next</button></span></footer>
    </section>
    {detail&&<div className="fixed inset-0 z-50 flex justify-end bg-slate-950/35"><div className="h-full w-full max-w-2xl overflow-y-auto bg-white p-5 shadow-2xl"><div className="mb-4 flex items-center justify-between"><h2 className="font-bold text-slate-900">Record detail</h2><button className="btn-secondary h-8 px-3" onClick={()=>setDetail(null)}>Close</button></div><RecordDetailCard data={toRecordDetailPart(detail)}/><button onClick={()=>navigate(`/command-center?module=${encodeURIComponent(moduleName)}&prompt=${encodeURIComponent(`show detail for ${detail.doctype} ${detail.name}`)}&autoRun=true`)} className="btn-primary mt-4 w-full">Ask AI about this record</button></div></div>}
  </div>
}

function formatValue(value:unknown){if(value===null||value===undefined||value==='')return '—';if(typeof value==='number')return new Intl.NumberFormat('en-IN').format(value);return String(value)}
function toRecordDetailPart(detail:DocumentDetailResponse):RecordDetailPart{return{type:'record_detail',doctype:detail.doctype,name:detail.name,title:detail.title,status:detail.status,workflow_state:detail.workflowState,docstatus:detail.docstatus,summary:detail.summary,fields:detail.fields,items:detail.items,available_workflow_actions:detail.availableWorkflowActions}}
