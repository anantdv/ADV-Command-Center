import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ReactNode } from 'react'
import { useMemo, useState } from 'react'
import { CheckCircle2, Circle, Clock3, FileDown, FileSpreadsheet, Filter, LayoutDashboard, ListFilter, LockKeyhole, Pin, ShieldAlert, Sparkles, XCircle } from 'lucide-react'
import { ToolExecutionCard } from './ToolExecutionCard'
import { GeneratedFileCard } from './GeneratedFileCard'
import { ConfirmationCard } from './ConfirmationCard'
import { MissingFieldsForm } from './MissingFieldsForm'
import { RecordPreviewCard } from './RecordPreviewCard'
import type { ChartPart, ChatMessagePart, ChatPermissionMeta, SourceMeta, SuggestedAction, TablePart } from '../../types/chat'
import { useAuthStore } from '../../store/useAuthStore'
import { formatCurrency } from '../../utils/formatters'
import { ColumnSelector } from '../reports/ColumnSelector'
import { RecordDetailCard } from '../results/RecordDetailCard'
import { chartPalette } from '../../theme/colors'
import { DocumentMappingPreview } from '../document-intake/DocumentMappingPreview'
import { ChildRowsResolutionCard } from './ChildRowsResolutionCard'
import { DraftFieldOptionsCard } from './DraftFieldOptionsCard'
import { DraftInspectionCard } from './DraftInspectionCard'
import { WorkflowActionConfirmDialog } from '../workflow/WorkflowActionConfirmDialog'
import { capabilities, isExternalErpNextAction } from '../../config/capabilities'

type Props = {
  parts?: ChatMessagePart[]
  fallback: string
  source?: SourceMeta | null
  permission?: ChatPermissionMeta | null
  actions?: SuggestedAction[]
  onAction?: (action:SuggestedAction, source?:SourceMeta|null)=>void
  onRowClick?: (row:Record<string,unknown>)=>void
  actionSlot?: ReactNode
}

export function StructuredMessageParts({ parts = [], fallback, source, permission, actions = [], onAction, onRowClick, actionSlot }: Props) {
  const currency=useAuthStore(state=>state.user?.companyCurrency)||'INR'
  const hasTextPart = parts.some(part => part.type === 'text')
  return <div className="space-y-3">
    {!hasTextPart&&<p className="max-w-[960px]">{fallback}</p>}
    {source&&<SourceStrip source={source} permission={permission}/>} 
    {parts.map((part,index) => {
      if(part.type==='text') return <p key={`text-${index}`} className="max-w-[960px]">{part.content}</p>
      if(part.type==='execution_plan') return <ExecutionPlanCard key={`plan-${index}`} part={part}/>
      if(part.type==='tool_call') return <ToolExecutionCard key={`tool-${index}`} part={part}/>
      if(part.type==='table') return <DynamicTable key={`table-${index}`} part={part} currency={currency} onRowClick={onRowClick}/>
      if(part.type==='chart') return <DynamicChart key={`chart-${index}`} part={part}/>
      if(part.type==='file') return <GeneratedFileCard key={`file-${index}`} part={part}/>
      if(part.type==='missing_fields') return <MissingFieldsForm key={`missing-${index}`} part={part}/>
      if(part.type==='record_preview') return <RecordPreviewCard key={`preview-${index}`} part={part}/>
      if(part.type==='draft_inspection') return <DraftInspectionCard key={`draft-inspection-${index}`} part={part}/>
      if(part.type==='record_detail') return <RecordDetailCard key={`detail-${index}`} data={part}/>
      if(part.type==='draft_field_options') return <DraftFieldOptionsCard key={`draft-options-${index}`} part={part}/>
      if(part.type==='confirmation') return <ConfirmationCard key={`confirm-${index}`} part={part}/>
      if(part.type==='workflow_confirmation') return <WorkflowConfirmationCard key={`workflow-confirm-${index}`} part={part}/>
      if(part.type==='ocr_mapping_preview') return <DocumentMappingPreview key={`ocr-${index}`} preview={part} onConfirm={()=>undefined} onCancel={()=>undefined}/>
      if(part.type==='child_rows_resolution_required') return <ChildRowsResolutionCard key={`resolve-${index}`} part={part}/>
      return null
    })}
    {permission&&!permission.allowed&&<div className="flex gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800"><ShieldAlert size={15} className="shrink-0"/><span>{permission.reason||'ERPNext restricted this request.'}</span></div>}
    {(actions.length>0||actionSlot)&&<div className="flex flex-wrap items-center gap-2"><SuggestedActions actions={actions} onAction={action=>onAction?.(action,source)}/>{actionSlot}</div>} 
  </div>
}

function WorkflowConfirmationCard({part}:{part:Extract<ChatMessagePart,{type:'workflow_confirmation'}>}){
  const [open,setOpen]=useState(false)
  const preview={doctype:part.doctype,name:part.name,action:part.action,current_state:part.current_state||part.currentState,next_state:part.next_state||part.nextState,title:part.title,summary:part.summary||{},confirmation_id:part.confirmation_id||part.confirmationId||''}
  return <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4">
    <p className="text-xs font-bold text-amber-800">Workflow confirmation required</p>
    <p className="mt-1 text-sm text-slate-700">Apply <span className="font-bold">{part.action}</span> to <span className="font-bold">{part.doctype} {part.name}</span>?</p>
    <p className="mt-1 text-xs text-slate-500">{part.current_state||part.currentState||'Current'} → {part.next_state||part.nextState||'Next'}</p>
    <button className="btn-primary mt-3 h-8 px-3 text-xs" onClick={()=>setOpen(true)}>Review and Confirm</button>
    <WorkflowActionConfirmDialog preview={preview} onClose={()=>setOpen(false)}/>
  </div>
}

function ExecutionPlanCard({part}:{part:Extract<ChatMessagePart,{type:'execution_plan'}>}){
  const statusClass={
    pending:'bg-slate-50 text-slate-500 ring-slate-200',
    running:'bg-indigo-50 text-indigo-700 ring-indigo-200',
    waiting_user:'bg-amber-50 text-amber-700 ring-amber-200',
    completed:'bg-emerald-50 text-emerald-700 ring-emerald-200',
    failed:'bg-rose-50 text-rose-700 ring-rose-200',
    cancelled:'bg-slate-100 text-slate-500 ring-slate-200',
    skipped:'bg-slate-50 text-slate-400 ring-slate-200',
  }[part.status]
  return <div className="rounded-xl border border-slate-200 bg-white p-4">
    <div className="flex flex-wrap items-center gap-2">
      <p className="text-xs font-bold text-slate-800">{part.title}</p>
      <span className={`rounded-full px-2 py-1 text-[9px] font-extrabold uppercase tracking-wider ring-1 ${statusClass}`}>{part.status.replace('_',' ')}</span>
      {part.resume_point&&<span className="text-[10px] font-semibold text-slate-400">Waiting for {part.resume_point.replace('_',' ')}</span>}
    </div>
    <div className="mt-3 grid gap-2 sm:grid-cols-2">
      {part.steps.map(step=><div key={step.id} className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-[11px] ${step.id===part.current_step_id?'border-indigo-200 bg-indigo-50/70':'border-slate-100 bg-slate-50/60'}`}>
        {step.status==='completed'?<CheckCircle2 size={14} className="text-emerald-600"/>:step.status==='failed'?<XCircle size={14} className="text-rose-600"/>:step.status==='running'||step.status==='waiting_user'?<Clock3 size={14} className="text-amber-600"/>:<Circle size={14} className="text-slate-300"/>}
        <div className="min-w-0"><p className="truncate font-bold text-slate-700">{step.label}</p><p className="truncate text-[9px] uppercase tracking-wider text-slate-400">{step.action} · {step.status.replace('_',' ')}</p></div>
      </div>)}
    </div>
  </div>
}

function SourceStrip({source,permission}:{source:SourceMeta;permission?:ChatPermissionMeta|null}){
  const filterCount=source.filters?Object.keys(source.filters).length:0
  return <div className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5">
    <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500"><LayoutDashboard size={12} className="text-indigo-500"/>{source.source_type}: {source.source_name}</span>
    {source.record_count!==null&&source.record_count!==undefined&&<span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-bold text-slate-500">{source.record_count} records</span>}
    {filterCount>0&&<span title={JSON.stringify(source.filters)} className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2 py-1 text-[10px] font-bold text-indigo-600"><Filter size={10}/>{filterCount} filter{filterCount===1?'':'s'}</span>}
    {permission?.confirmation_required&&<span className="ml-auto rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-700">Confirmation required</span>}
  </div>
}

function DynamicTable({part,currency,onRowClick}:{part:TablePart;currency:string;onRowClick?: (row:Record<string,unknown>)=>void}){
  const [customize,setCustomize]=useState(false)
  const publicColumns=useMemo(()=>part.columns.filter(column=>!column.key.startsWith('_')),[part.columns])
  const [visible,setVisible]=useState<string[]>(publicColumns.map(column=>column.key))
  const available=useMemo(()=>publicColumns.map(column=>({key:column.key,label:column.label,fieldtype:column.type||'Data',visible:true,source:'doctype' as const})),[publicColumns])
  const columns=publicColumns.filter(column=>visible.includes(column.key))
  return <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
    <div className="flex items-center justify-between border-b bg-slate-50/70 px-4 py-3"><div><p className="text-xs font-bold text-slate-800">{part.title}</p><p className="mt-0.5 text-[10px] text-slate-400">Showing {part.rows.length}{part.total_rows!==null&&part.total_rows!==undefined?` of ${part.total_rows}`:''} rows · {columns.length} columns</p></div><button onClick={()=>setCustomize(value=>!value)} className="btn-secondary h-8 px-2 text-xs"><ListFilter size={14}/>Columns</button></div>
    {customize&&<div className="border-b p-3"><ColumnSelector columns={available} selected={visible} onApply={columns=>{setVisible(columns);setCustomize(false)}}/></div>}
    {part.rows.length===0?<div className="px-4 py-8 text-center text-xs text-slate-400">No records matched this query.</div>:<div className="overflow-x-auto scrollbar-thin"><table className="w-full min-w-[620px] text-left"><thead><tr className="border-b border-slate-100">{columns.map(column=><th key={column.key} className="whitespace-nowrap px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">{column.label}</th>)}</tr></thead><tbody>{part.rows.map((row,rowIndex)=>{const meta=row._meta as {clickable?:boolean;doctype?:string;name?:string}|undefined;const clickable=Boolean(meta?.clickable&&meta.doctype&&meta.name);return <tr key={String(row.name||row.id||rowIndex)} onClick={()=>clickable&&onRowClick?.(row)} className={`border-b border-slate-100 last:border-0 ${clickable?'cursor-pointer hover:bg-indigo-50/70':'hover:bg-slate-50/70'}`}>{columns.map(column=><td key={column.key} className="whitespace-nowrap px-4 py-3 text-xs text-slate-600">{formatCell(row[column.key],column.type,column.key,currency)}</td>)}</tr>})}</tbody></table></div>}
  </div>
}

function formatCell(value:unknown,type:string,key:string,currency:string){
  if(value===null||value===undefined||value==='') return <span className="text-slate-300">—</span>
  if(typeof value==='boolean') return value?'Yes':'No'
  if(type==='number'&&typeof value==='number') return <span className="font-semibold text-slate-800">{key.includes('amount')||key.includes('total')?formatCurrency(value,currency):new Intl.NumberFormat('en-IN').format(value)}</span>
  if(key==='name') return <span className="font-semibold text-indigo-600">{String(value)}</span>
  return String(value)
}

function DynamicChart({part}:{part:ChartPart}){
  if(!part.data?.length||!part.x_key||!part.y_key) return null
  const rows=normalizeChartRows(part)
  const common={data:rows,margin:{top:8,right:8,left:4,bottom:20}}
  const tooltipFormatter=(value:unknown)=>typeof value==='number'?formatCompactNumber(value):String(value)
  const axes=<><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0"/><XAxis dataKey={part.x_key} axisLine={false} tickLine={false} tick={{fontSize:10,fill:'#64748b'}} angle={rows.length>6?-18:0} textAnchor={rows.length>6?'end':'middle'} height={rows.length>6?42:28}/><YAxis axisLine={false} tickLine={false} tick={{fontSize:10,fill:'#64748b'}} tickFormatter={formatCompactNumber}/><Tooltip formatter={tooltipFormatter} contentStyle={{borderRadius:10,fontSize:11,border:'1px solid #e2e8f0'}}/></>
  return <div className="rounded-xl border border-slate-200 bg-white p-4"><div className="mb-3 flex items-center justify-between"><div><p className="text-xs font-bold text-slate-800">{part.title||'Chart preview'}</p><p className="mt-0.5 text-[10px] text-slate-400">Generated from the active result context</p></div><span className="rounded-full bg-indigo-50 px-2 py-1 text-[9px] font-bold text-indigo-600"><Sparkles size={9} className="mr-1 inline"/>Generated by Tinni</span></div><div className="h-56"><ResponsiveContainer width="100%" height="100%">{part.chart_type==='line'?<LineChart {...common}>{axes}<Line type="monotone" dataKey={part.y_key} stroke={chartPalette[0]} strokeWidth={2.5} dot={{r:3}}/></LineChart>:part.chart_type==='area'?<AreaChart {...common}>{axes}<Area type="monotone" dataKey={part.y_key} stroke={chartPalette[4]} fill={`${chartPalette[4]}24`} strokeWidth={2}/></AreaChart>:part.chart_type==='pie'||part.chart_type==='donut'?<PieChart><Tooltip formatter={tooltipFormatter}/><Pie data={rows} dataKey={part.y_key} nameKey={part.x_key} innerRadius={part.chart_type==='donut'?48:0} outerRadius={78} label>{rows.map((_,index)=><Cell key={index} fill={chartPalette[index%chartPalette.length]}/>)}</Pie></PieChart>:<BarChart {...common}>{axes}<Bar dataKey={part.y_key} radius={[6,6,0,0]}>{rows.map((_,index)=><Cell key={index} fill={chartPalette[index%chartPalette.length]}/>)}</Bar></BarChart>}</ResponsiveContainer></div></div>
}

function normalizeChartRows(part:ChartPart){
  const rows=[...(part.data||[])]
  const xKey=part.x_key||''
  const yKey=part.y_key||''
  const hasPeriods=rows.some(row=>parsePeriodLabel(row[xKey])!==null)
  if(hasPeriods&&['line','area','bar'].includes(part.chart_type||'')){
    return rows.sort((a,b)=>(parsePeriodLabel(a[xKey])?.getTime()??Number.MAX_SAFE_INTEGER)-(parsePeriodLabel(b[xKey])?.getTime()??Number.MAX_SAFE_INTEGER))
  }
  if(part.chart_type==='bar'&&yKey){
    return rows.sort((a,b)=>toNumber(b[yKey])-toNumber(a[yKey]))
  }
  return rows
}

function parsePeriodLabel(value:unknown){
  if(!value)return null
  const text=String(value).trim()
  const quarter=text.match(/^Q([1-4])\s+(\d{4})$/i)
  if(quarter)return new Date(Number(quarter[2]),(Number(quarter[1])-1)*3,1)
  const parsed=Date.parse(text.length===7&&/^\d{4}-\d{2}$/.test(text)?`${text}-01`:text)
  if(!Number.isNaN(parsed))return new Date(parsed)
  const month=text.match(/^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})$/i)
  if(month){
    const monthIndex=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'].indexOf(month[1].slice(0,3).toLowerCase())
    return new Date(Number(month[2]),monthIndex,1)
  }
  if(/^\d{4}$/.test(text))return new Date(Number(text),0,1)
  return null
}

function toNumber(value:unknown){
  if(typeof value==='number')return value
  if(typeof value==='string'){
    const parsed=Number(value.replace(/[₹,\s]/g,''))
    return Number.isFinite(parsed)?parsed:0
  }
  return 0
}

function formatCompactNumber(value:unknown){
  const numeric=toNumber(value)
  return new Intl.NumberFormat(undefined,{notation:'compact',maximumFractionDigits:1}).format(numeric)
}

const actionIcons:Record<string,typeof Pin>={generate_pdf:FileDown,export_excel:FileSpreadsheet,export_csv:FileSpreadsheet,download_file:FileDown,open_library:FileSpreadsheet,generate_another:Sparkles,pin_overview:Pin,refine_filters:Filter,view_related:ListFilter,open_module:LayoutDashboard,prepare_later:LockKeyhole}
function SuggestedActions({actions,onAction}:{actions:SuggestedAction[];onAction:(action:SuggestedAction)=>void}){
  const visible=actions.filter(action=>capabilities.erpnextExternalLinksEnabled||!isExternalErpNextAction(action.action_type))
  return <>{visible.map(action=>{const Icon=actionIcons[action.action_type]||Sparkles;return <button key={`${action.action_type}-${action.label}`} type="button" onClick={()=>onAction(action)} disabled={action.disabled} title={action.reason||action.label} className="btn-secondary disabled:cursor-not-allowed disabled:opacity-45"><Icon size={14}/>{action.label}</button>})}</>
}
