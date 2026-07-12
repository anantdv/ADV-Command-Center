import { LayoutDashboard, Pin } from 'lucide-react'
import { ResultActionDialog } from './ResultActionDialog'

export function PinTargetDialog({open,onClose,onPin}:{open:boolean;onClose:()=>void;onPin?:(target:string)=>void}){
  return <ResultActionDialog open={open} title="Pin Result" description="Choose where this report/chart should appear. Pinning still uses the existing backend permission-safe dashboard endpoint." onClose={onClose}>
    <div className="grid gap-2 sm:grid-cols-2">
      <button className="rounded-xl border border-indigo-200 bg-indigo-50 p-4 text-left text-indigo-700" onClick={()=>onPin?.('overview')}><LayoutDashboard size={18}/><p className="mt-2 text-xs font-bold">Overview</p></button>
      <button className="rounded-xl border border-slate-200 p-4 text-left text-slate-600" onClick={()=>onPin?.('module')}><Pin size={18}/><p className="mt-2 text-xs font-bold">Module dashboard</p></button>
    </div>
  </ResultActionDialog>
}
