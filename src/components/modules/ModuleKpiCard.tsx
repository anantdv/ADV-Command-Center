import { ArrowUpRight } from 'lucide-react'
import { formatCurrency } from '../../utils/formatters'
import type { ModuleKpi } from '../../types/module'

export function ModuleKpiCard({ kpi, onClick }: { kpi: ModuleKpi; onClick?: (prompt: string) => void }) {
  const value = kpi.valueType === 'currency' && typeof kpi.value === 'number' ? formatCurrency(kpi.value, kpi.currency || 'INR') : String(kpi.value)
  return <button type="button" onClick={()=>kpi.actionPrompt&&onClick?.(kpi.actionPrompt)} className="card p-4 text-left transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md">
    <div className="flex items-start justify-between gap-3">
      <div>
        <p className="text-xs font-bold text-slate-500">{kpi.label}</p>
        <p className="mt-2 font-[Manrope] text-2xl font-bold text-slate-950">{value}</p>
      </div>
      <span className="flex size-8 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600"><ArrowUpRight size={15}/></span>
    </div>
    {kpi.sourceDoctype&&<p className="mt-3 text-[10px] font-semibold text-slate-400">Source: {kpi.sourceDoctype}</p>}
  </button>
}
