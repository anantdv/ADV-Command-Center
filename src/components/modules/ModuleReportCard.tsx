import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ModuleReport } from '../../types/module'
import { formatCurrency } from '../../utils/formatters'
import { chartPalette } from '../../theme/colors'
import { analyticsService } from '../../services/analyticsService'
import { useState } from 'react'
import type { AnalyticsResult } from '../../types/analytics'

export function ModuleReportCard({ report, onPrompt }: { report: ModuleReport; onPrompt?: (prompt: string) => void }) {
  const [result,setResult]=useState<AnalyticsResult|null>(null)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState<string|null>(null)
  const runInline=async()=>{if(report.reportType!=='analytics')return onPrompt?.(report.actionPrompt||`show ${report.title.toLowerCase()}`);setLoading(true);setError(null);try{setResult(await analyticsService.runByKey(report.id,{chartType:report.chartType||undefined,limit:20}))}catch(err){setError(err instanceof Error?err.message:'Could not run analytics.')}finally{setLoading(false)}}
  const activeRows = result?.rows || report.data
  const activeColumns = result?.columns || report.columns
  const activeChart = result?.chart
  const keys = activeRows[0] ? Object.keys(activeRows[0]) : []
  const xKey = keys[0]
  const yKey = keys.find(key => typeof activeRows[0]?.[key] === 'number') || keys[1]
  const chartType = String(activeChart?.chart_type || activeChart?.chartType || report.chartType || '')
  const chartRows = (activeChart?.data as Array<Record<string,unknown>> | undefined) || activeRows
  const chartX = String(activeChart?.x_key || activeChart?.name_key || xKey || '')
  const chartY = String(activeChart?.y_key || activeChart?.value_key || yKey || '')
  return <section className="card overflow-hidden">
    <div className="flex items-start justify-between gap-3 border-b px-4 py-3">
      <div><h3 className="text-sm font-bold text-slate-900">{report.title}</h3><p className="mt-1 text-[10px] text-slate-400">{report.sourceDoctype || report.reportName || 'ERPNext report'}</p></div>
      <div className="flex gap-1">{report.reportType==='analytics'&&<button onClick={()=>void runInline()} disabled={loading} className="btn-primary h-8 px-2 text-xs">{loading?'Running…':'Run'}</button>}{report.actionPrompt&&<button onClick={()=>onPrompt?.(report.actionPrompt!)} className="btn-secondary h-8 px-2 text-xs">Open</button>}</div>
    </div>
    {result?.summary&&<p className="border-b bg-slate-50 px-4 py-2 text-xs text-slate-500">{result.summary}</p>}
    {error&&<p className="border-b bg-rose-50 px-4 py-2 text-xs font-semibold text-rose-700">{error}</p>}
    {(report.reportType==='chart'||result?.chart)&&chartRows.length>0&&chartX&&chartY&&chartType!=='table'?<div className="h-56 p-4">
      <ResponsiveContainer width="100%" height="100%">
        {chartType==='line'?<LineChart data={chartRows}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey={chartX} tick={{fontSize:10}}/><YAxis tick={{fontSize:10}}/><Tooltip/>{((activeChart?.series as Array<Record<string,string>>|undefined)||[{data_key:chartY,label:chartY}]).map((series,index)=><Line key={String(series.data_key)} type="monotone" dataKey={String(series.data_key)} name={String(series.label||series.data_key)} stroke={chartPalette[index%chartPalette.length]} strokeWidth={2}/>)}</LineChart>:chartType==='pie'||chartType==='donut'?<PieChart><Tooltip/><Pie data={chartRows} dataKey={chartY} nameKey={chartX} outerRadius={80} label>{chartRows.map((_,index)=><Cell key={index} fill={chartPalette[index%chartPalette.length]}/>)}</Pie></PieChart>:<BarChart data={chartRows}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey={chartX} tick={{fontSize:10}}/><YAxis tick={{fontSize:10}}/><Tooltip/><Bar dataKey={chartY} radius={[6,6,0,0]}>{chartRows.map((_,index)=><Cell key={index} fill={chartPalette[index%chartPalette.length]}/>)}</Bar></BarChart>}
      </ResponsiveContainer>
    </div>:<div className="overflow-x-auto p-4"><table className="w-full min-w-[520px] text-left text-xs"><thead><tr>{(activeColumns.length?activeColumns:keys.map(key=>({key,label:key.replace(/_/g,' ')}))).slice(0,6).map(column=><th key={column.key} className="px-3 py-2 text-[10px] uppercase tracking-wide text-slate-400">{column.label}</th>)}</tr></thead><tbody>{activeRows.slice(0,8).map((row,index)=><tr key={String(row.name||index)} className="border-t">{(activeColumns.length?activeColumns:keys.map(key=>({key,label:key}))).slice(0,6).map(column=><td key={column.key} className="px-3 py-2 text-slate-600">{formatValue(column.key,row[column.key])}</td>)}</tr>)}</tbody></table>{activeRows.length===0&&<p className="py-8 text-center text-xs text-slate-400">{loading?'Loading analytics…':'No data loaded yet. Click Run to preview.'}</p>}</div>}
  </section>
}

function formatValue(key:string,value:unknown){
  if(value===null||value===undefined||value==='')return '—'
  if(typeof value==='number'&&/(amount|total|outstanding)/i.test(key))return formatCurrency(value,'INR')
  if(typeof value==='number')return new Intl.NumberFormat('en-IN').format(value)
  return String(value)
}
