import { ResultActionDialog } from './ResultActionDialog'

export function RefineFiltersDialog({open,filters,onClose}:{open:boolean;filters?:Record<string,unknown>;onClose:()=>void}){
  return <ResultActionDialog open={open} title="Refine Filters" description="Review the filters attached to this result. Applying new filters will rerun through the safe chat/report pipeline in the next iteration." onClose={onClose}>
    <pre className="max-h-56 overflow-auto rounded-xl bg-slate-950 p-3 text-[11px] text-slate-100">{JSON.stringify(filters||{},null,2)}</pre>
    <div className="mt-4 flex justify-end"><button className="btn-primary h-9 px-4 text-xs" onClick={onClose}>Done</button></div>
  </ResultActionDialog>
}
