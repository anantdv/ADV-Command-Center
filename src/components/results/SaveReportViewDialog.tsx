import { useState } from 'react'
import { ResultActionDialog } from './ResultActionDialog'

export function SaveReportViewDialog({open,onClose}:{open:boolean;onClose:()=>void}){
  const [name,setName]=useState('My report view')
  return <ResultActionDialog open={open} title="Save Report View" description="Save this result configuration for quick reuse. This is a UI placeholder until the saved-view endpoint is wired to this action." onClose={onClose}>
    <label className="text-xs font-bold text-slate-600">View name</label>
    <input value={name} onChange={event=>setName(event.target.value)} className="mt-2 h-10 w-full rounded-xl border border-slate-200 px-3 text-sm outline-none focus:border-indigo-300"/>
    <div className="mt-4 flex justify-end"><button className="btn-primary h-9 px-4 text-xs" onClick={onClose}>Save</button></div>
  </ResultActionDialog>
}
