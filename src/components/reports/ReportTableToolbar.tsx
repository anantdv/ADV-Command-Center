import { SlidersHorizontal } from 'lucide-react'

export function ReportTableToolbar({title,onCustomize,onExport}:{title:string;onCustomize?:()=>void;onExport?:(format:'xlsx'|'csv'|'pdf')=>void}){
 return <div className="mb-3 flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-bold text-slate-900">{title}</h3><div className="flex flex-wrap gap-2">{onCustomize&&<button onClick={onCustomize} className="btn-secondary h-9 px-3 text-xs"><SlidersHorizontal size={14}/> Columns</button>}{onExport&&<><button onClick={()=>onExport('xlsx')} className="btn-secondary h-9 px-3 text-xs">Excel</button><button onClick={()=>onExport('csv')} className="btn-secondary h-9 px-3 text-xs">CSV</button><button onClick={()=>onExport('pdf')} className="btn-secondary h-9 px-3 text-xs">PDF</button></>}</div></div>
}
