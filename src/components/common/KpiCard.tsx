import { ArrowDownRight, ArrowUpRight, type LucideIcon } from 'lucide-react'

const tones: Record<string, string> = {
  indigo: 'bg-indigo-50 text-indigo-600', blue: 'bg-blue-50 text-blue-600', amber: 'bg-amber-50 text-amber-600',
  rose: 'bg-rose-50 text-rose-600', emerald: 'bg-emerald-50 text-emerald-600', violet: 'bg-violet-50 text-violet-600',
}
export function KpiCard({ label, value, change, trend = 'up', icon: Icon, accent = 'indigo' }: { label: string; value: string; change?: string; trend?: 'up' | 'down'; icon?: LucideIcon; accent?: string }) {
  return <div className="card group p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-lg sm:p-5">
    <div className="flex items-start justify-between">
      <div className={`flex size-10 items-center justify-center rounded-xl ${tones[accent] || tones.indigo}`}>{Icon && <Icon size={19} />}</div>
      {change && <div className={`flex items-center gap-1 rounded-full px-2 py-1 text-xs font-bold ${trend === 'up' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
        {trend === 'up' ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}{change}
      </div>}
    </div>
    <p className="mt-5 text-xs font-semibold text-slate-500">{label}</p>
    <p className="mt-1 font-[Manrope] text-xl font-bold tracking-tight text-slate-900">{value}</p>
    {change && <p className="mt-2 text-[11px] text-slate-400">vs previous month</p>}
  </div>
}
