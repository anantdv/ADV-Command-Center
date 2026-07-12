import { CalendarDays, Check, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { useGlobalDateRange } from '../../hooks/useGlobalDateRange'
import type { AppDateRange, DateRangePreset } from '../../types/dateRange'

const iso=(date:Date)=>`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`
const displayDate=(value:string)=>new Intl.DateTimeFormat('en-IN',{day:'2-digit',month:'short',year:'2-digit'}).format(new Date(`${value}T00:00:00`))
const labels: Record<DateRangePreset,string> = { today:'Today', this_week:'This Week', this_month:'This Month', this_quarter:'This Quarter', this_year:'This Year', last_month:'Last Month', last_quarter:'Last Quarter', last_year:'Last Year', custom:'Custom Range' }

function presetRange(preset: DateRangePreset): AppDateRange {
  const now = new Date()
  const startOfWeek = new Date(now); startOfWeek.setDate(now.getDate() - ((now.getDay()+6)%7))
  let from = new Date(now), to = new Date(now)
  if (preset === 'today') from = new Date(now)
  else if (preset === 'this_week') from = startOfWeek
  else if (preset === 'this_month') from = new Date(now.getFullYear(), now.getMonth(), 1)
  else if (preset === 'this_quarter') from = new Date(now.getFullYear(), Math.floor(now.getMonth()/3)*3, 1)
  else if (preset === 'this_year') from = new Date(now.getFullYear(), 0, 1)
  else if (preset === 'last_month') { from = new Date(now.getFullYear(), now.getMonth()-1, 1); to = new Date(now.getFullYear(), now.getMonth(), 0) }
  else if (preset === 'last_quarter') { const q = Math.floor(now.getMonth()/3)-1; from = new Date(now.getFullYear(), q*3, 1); to = new Date(now.getFullYear(), q*3+3, 0) }
  else if (preset === 'last_year') { from = new Date(now.getFullYear()-1, 0, 1); to = new Date(now.getFullYear()-1, 11, 31) }
  return { from: iso(from), to: iso(to), label: labels[preset], preset }
}

export function GlobalDateRangePicker() {
  const [open,setOpen]=useState(false)
  const {dateRange,setDateRange}=useGlobalDateRange()
  const choose=(preset:DateRangePreset)=>{setDateRange(presetRange(preset));setOpen(false)}
  return <div className="relative hidden lg:block"><button onClick={()=>setOpen(value=>!value)} aria-expanded={open} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"><CalendarDays size={15} className="text-slate-400"/>{displayDate(dateRange.from)} – {displayDate(dateRange.to)}<ChevronDown size={13} className={`text-slate-400 transition ${open?'rotate-180':''}`}/></button>{open&&<div className="absolute right-0 top-12 w-72 rounded-2xl border bg-white p-3 shadow-xl"><p className="px-2 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">Date range</p>{(['today','this_week','this_month','this_quarter','this_year','last_month','last_quarter','last_year'] as DateRangePreset[]).map(preset=><button key={preset} onClick={()=>choose(preset)} className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-xs font-semibold text-slate-600 hover:bg-slate-50">{labels[preset]}{(dateRange.preset===preset||dateRange.label===labels[preset])&&<Check size={13} className="text-indigo-600"/>}</button>)}<div className="mt-2 grid grid-cols-2 gap-2 border-t pt-3"><label className="text-[10px] font-bold text-slate-400">From<input type="date" value={dateRange.from} onChange={event=>setDateRange({...dateRange,from:event.target.value,label:'Custom Range',preset:'custom'})} className="mt-1 h-9 w-full rounded-lg border px-2 text-[11px] text-slate-600"/></label><label className="text-[10px] font-bold text-slate-400">To<input type="date" min={dateRange.from} value={dateRange.to} onChange={event=>setDateRange({...dateRange,to:event.target.value,label:'Custom Range',preset:'custom'})} className="mt-1 h-9 w-full rounded-lg border px-2 text-[11px] text-slate-600"/></label></div></div>}</div>
}
