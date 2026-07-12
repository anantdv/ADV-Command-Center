import { BarChart3, LineChart, PieChart, Waves } from 'lucide-react'
import { ResultActionDialog } from './ResultActionDialog'

const options=[
  {type:'bar',label:'Bar',icon:BarChart3},
  {type:'line',label:'Line',icon:LineChart},
  {type:'area',label:'Area',icon:Waves},
  {type:'pie',label:'Pie',icon:PieChart},
  {type:'donut',label:'Donut',icon:PieChart},
] as const

export function ChangeChartTypeDialog({open,currentType,onApply,onClose}:{open:boolean;currentType?:string|null;onApply:(chartType:string)=>void;onClose:()=>void}){
  return <ResultActionDialog open={open} title="Change Chart Type" description="Choose a visualization for this active chart result. This does not change ERPNext data." onClose={onClose}>
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {options.map(option=>{const Icon=option.icon;const active=currentType===option.type;return <button key={option.type} type="button" onClick={()=>onApply(option.type)} className={`rounded-xl border p-4 text-left transition ${active?'border-indigo-300 bg-indigo-50 text-indigo-700':'border-slate-200 bg-white text-slate-700 hover:border-indigo-200 hover:bg-indigo-50/50'}`}>
        <Icon size={18}/>
        <p className="mt-3 text-xs font-bold">{option.label}</p>
      </button>})}
    </div>
  </ResultActionDialog>
}
