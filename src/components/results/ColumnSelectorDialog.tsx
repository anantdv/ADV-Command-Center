import { ResultActionDialog } from './ResultActionDialog'

export function ColumnSelectorDialog({open,columns=[],onClose}:{open:boolean;columns?:string[];onClose:()=>void}){
  return <ResultActionDialog open={open} title="Change Columns" description="Column customization for the active result. Full server-side rerun support will be added in the report view stage." onClose={onClose}>
    <div className="space-y-2">
      {(columns.length?columns:['name','status','grand_total']).map(column=><label key={column} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600"><input type="checkbox" defaultChecked className="rounded border-slate-300"/>{column.replaceAll('_',' ')}</label>)}
    </div>
    <div className="mt-4 flex justify-end"><button className="btn-primary h-9 px-4 text-xs" onClick={onClose}>Apply</button></div>
  </ResultActionDialog>
}
