import { Bar, BarChart, CartesianGrid, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ModuleReport } from '../../types/module'
import { formatCurrency } from '../../utils/formatters'

export function ModuleReportCard({ report, onPrompt }: { report: ModuleReport; onPrompt?: (prompt: string) => void }) {
  const keys = report.data[0] ? Object.keys(report.data[0]) : []
  const xKey = keys[0]
  const yKey = keys.find(key => typeof report.data[0]?.[key] === 'number') || keys[1]
  return <section className="card overflow-hidden">
    <div className="flex items-start justify-between gap-3 border-b px-4 py-3">
      <div><h3 className="text-sm font-bold text-slate-900">{report.title}</h3><p className="mt-1 text-[10px] text-slate-400">{report.sourceDoctype || report.reportName || 'ERPNext report'}</p></div>
      {report.actionPrompt&&<button onClick={()=>onPrompt?.(report.actionPrompt!)} className="btn-secondary h-8 px-2 text-xs">Open</button>}
    </div>
    {report.reportType==='chart'&&report.data.length>0&&xKey&&yKey?<div className="h-56 p-4">
      <ResponsiveContainer width="100%" height="100%">
        {report.chartType==='line'?<LineChart data={report.data}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey={xKey} tick={{fontSize:10}}/><YAxis tick={{fontSize:10}}/><Tooltip/><Line type="monotone" dataKey={yKey} stroke="#6366f1" strokeWidth={2}/></LineChart>:report.chartType==='pie'?<PieChart><Tooltip/><Pie data={report.data} dataKey={yKey} nameKey={xKey} outerRadius={80} fill="#6366f1" label/></PieChart>:<BarChart data={report.data}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey={xKey} tick={{fontSize:10}}/><YAxis tick={{fontSize:10}}/><Tooltip/><Bar dataKey={yKey} fill="#6366f1" radius={[6,6,0,0]}/></BarChart>}
      </ResponsiveContainer>
    </div>:<div className="overflow-x-auto p-4"><table className="w-full min-w-[520px] text-left text-xs"><thead><tr>{(report.columns.length?report.columns:keys.map(key=>({key,label:key.replace(/_/g,' ')}))).slice(0,6).map(column=><th key={column.key} className="px-3 py-2 text-[10px] uppercase tracking-wide text-slate-400">{column.label}</th>)}</tr></thead><tbody>{report.data.slice(0,8).map((row,index)=><tr key={String(row.name||index)} className="border-t">{(report.columns.length?report.columns:keys.map(key=>({key,label:key}))).slice(0,6).map(column=><td key={column.key} className="px-3 py-2 text-slate-600">{formatValue(column.key,row[column.key])}</td>)}</tr>)}</tbody></table>{report.data.length===0&&<p className="py-8 text-center text-xs text-slate-400">No data available.</p>}</div>}
  </section>
}

function formatValue(key:string,value:unknown){
  if(value===null||value===undefined||value==='')return '—'
  if(typeof value==='number'&&/(amount|total|outstanding)/i.test(key))return formatCurrency(value,'INR')
  if(typeof value==='number')return new Intl.NumberFormat('en-IN').format(value)
  return String(value)
}
